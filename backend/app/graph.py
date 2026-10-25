import os
import pickle
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.schemas import JobState
from app.nodes import (
    strategist, researcher, verifier, planner, scriptwriter,
    critic, human_gate_node, visual_planner, voice_director,
    render_video, qa_gate, metadata_agent, publisher, analyst
)

logger = logging.getLogger(__name__)

class DurableFileCheckpointer(MemorySaver):
    """
    Thread-safe, file-backed durable checkpointer for LangGraph.
    Preserves interrupted and completed job states across process restarts.
    """
    def __init__(self, filepath: str = "data/checkpoints.pkl"):
        super().__init__()
        self.filepath = filepath
        dir_name = os.path.dirname(os.path.abspath(filepath))
        os.makedirs(dir_name, exist_ok=True)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'rb') as f:
                    data = pickle.load(f)
                    for k, v in data.get('storage', {}).items():
                        if isinstance(v, dict):
                            self.storage[k].update(v)
                        else:
                            self.storage[k] = v
                    for k, v in data.get('writes', {}).items():
                        if isinstance(v, dict):
                            self.writes[k].update(v)
                        else:
                            self.writes[k] = v
                logger.info(f"Loaded existing durable checkpoints from {filepath}")
            except Exception as e:
                logger.warning(f"Could not load checkpoint file ({e}). Starting fresh.")

    def _save_to_disk(self):
        try:
            def _clean(val):
                if isinstance(val, dict):
                    return {k: _clean(v) for k, v in val.items()}
                if isinstance(val, (list, tuple)):
                    return [_clean(v) for v in val]
                return val

            clean_storage = _clean(self.storage)
            clean_writes = _clean(self.writes)
            with open(self.filepath, 'wb') as f:
                pickle.dump({'storage': clean_storage, 'writes': clean_writes}, f)
        except Exception as e:
            logger.warning(f"Failed to persist checkpoint to disk: {e}")

    def put(self, config, checkpoint, metadata, new_versions):
        res = super().put(config, checkpoint, metadata, new_versions)
        self._save_to_disk()
        return res

def route_after_critic(state: JobState):
    """
    Conditional routing after Critic Gate:
    - If autonomy <= 1 (Manual or Script Gate enabled): route to human review.
    - If script passed critic and autonomy >= 2: proceed directly to visuals.
    - If critic failed and rewrite_count >= 3: escalate to human review.
    - Otherwise: loop back to scriptwriter for targeted rewrite.
    """
    autonomy = state.get('autonomy', 1)
    c = state.get('critic', {})
    critic_passed = (
        bool(c.get('pass')) or
        state.get('critic_status') == 'pass' or
        (isinstance(state.get('critic_score'), (int, float)) and state.get('critic_score', 0) >= 75)
    )
    rewrites = state.get('rewrite_count', 0) or state.get('retry_counts', {}).get('script_rewrite', 0)
    
    # Sensitive human gate enabled for autonomy levels 0 and 1
    if autonomy <= 1:
        return 'human_review'
        
    if critic_passed:
        return 'visuals'
        
    if rewrites >= 3:
        return 'human_review'
        
    return 'scriptwriter'

def route_after_human(state: JobState):
    """Route after human review decision."""
    approval = state.get('human_approval', {})
    decision = approval.get('status') or approval.get('action') or 'approved'
    if decision in ('rejected', 'reject'):
        return END
    if decision in ('revision_requested', 'request_revision'):
        return 'scriptwriter'
    return 'visuals'

def route_after_qa(state: JobState):
    """
    Conditional routing on QA validation results:
    - If passed: proceed to metadata.
    - If failed and under retry limit (<= 2): route back to render or voice.
    - If failed and retries exhausted: escalate to human review.
    """
    qa_data = state.get('qa', {})
    qa_passed = (
        bool(qa_data.get('passed')) or
        state.get('qa_status') == 'pass' or
        (isinstance(state.get('quality_report'), dict) and state['quality_report'].get('passed') is True)
    )
    if qa_passed:
        return 'metadata'
        
    retries = state.get('retry_counts', {}).get('render', 0)
    if retries < 2:
        report = state.get('quality_report', {})
        if report and (not report.get('has_audio') and not report.get('has_video')):
            return 'voice'
        return 'render'
        
    return 'human_review'

# Build 14-Stage LangGraph
g = StateGraph(JobState)

# 1. Register all 14 stages
g.add_node('strategist', strategist)
g.add_node('researcher', researcher)
g.add_node('verifier', verifier)
g.add_node('planner', planner)
g.add_node('scriptwriter', scriptwriter)
g.add_node('critic', critic)
g.add_node('human_review', human_gate_node)
g.add_node('visuals', visual_planner)
g.add_node('voice', voice_director)
g.add_node('render', render_video)
g.add_node('qa_gate', qa_gate)
g.add_node('metadata', metadata_agent)
g.add_node('publish', publisher)
g.add_node('analyst', analyst)

# 2. Sequential research and scripting edges
g.set_entry_point('strategist')
g.add_edge('strategist', 'researcher')
g.add_edge('researcher', 'verifier')
g.add_edge('verifier', 'planner')
g.add_edge('planner', 'scriptwriter')
g.add_edge('scriptwriter', 'critic')

# 3. Critic conditional edge
g.add_conditional_edges('critic', route_after_critic, {
    'visuals': 'visuals',
    'human_review': 'human_review',
    'scriptwriter': 'scriptwriter'
})

# 4. Human gate routing
g.add_conditional_edges('human_review', route_after_human, {
    'visuals': 'visuals',
    'scriptwriter': 'scriptwriter',
    END: END
})

# 5. Media assembly & rendering edges
g.add_edge('visuals', 'voice')
g.add_edge('voice', 'render')
g.add_edge('render', 'qa_gate')

# 6. QA Gate recovery edge
g.add_conditional_edges('qa_gate', route_after_qa, {
    'metadata': 'metadata',
    'render': 'render',
    'voice': 'voice',
    'human_review': 'human_review'
})

# 7. Distribution and analytics edges
g.add_edge('metadata', 'publish')
g.add_edge('publish', 'analyst')
g.add_edge('analyst', END)

# 8. Durable file checkpointer and compilation
checkpointer = DurableFileCheckpointer("data/checkpoints.pkl")
app_graph = g.compile(
    checkpointer=checkpointer,
    interrupt_before=['human_review']
)
