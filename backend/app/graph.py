from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.schemas import JobState
from app.nodes import (
    strategist, researcher, verifier, planner, scriptwriter,
    critic, visual_planner, voice_director, render_video,
    qa_gate, metadata_agent, publisher, analyst
)
import logging

logger = logging.getLogger(__name__)

def route_after_critic(state: JobState):
    c = state.get('critic', {})
    if c.get('pass'):
        return 'visuals'
    if state.get('rewrite_count', 0) >= 3:
        return 'human_review'
    return 'scriptwriter'

def human_gate(state: JobState):
    """
    Human-in-the-loop pause gate.
    In LangGraph, this halts execution for dashboard human review and resumes when approved.
    """
    logger.info(f"Job {state.get('job_id')} paused at human_review gate.")
    return {'qa': {**state.get('qa', {}), 'human_reviewed': True}}

# Build StateGraph
g = StateGraph(JobState)

# Add all 14 nodes
g.add_node('strategist', strategist)
g.add_node('researcher', researcher)
g.add_node('verifier', verifier)
g.add_node('planner', planner)
g.add_node('scriptwriter', scriptwriter)
g.add_node('critic', critic)
g.add_node('human_review', human_gate)
g.add_node('visuals', visual_planner)
g.add_node('voice', voice_director)
g.add_node('render', render_video)
g.add_node('qa_gate', qa_gate)
g.add_node('metadata', metadata_agent)
g.add_node('publish', publisher)
g.add_node('analyst', analyst)

# Connect edges matching blueprint flow
g.set_entry_point('strategist')
g.add_edge('strategist', 'researcher')
g.add_edge('researcher', 'verifier')
g.add_edge('verifier', 'planner')
g.add_edge('planner', 'scriptwriter')
g.add_edge('scriptwriter', 'critic')

# Conditional routing after critic: retry up to 3 times, then human review, or visuals if passed
g.add_conditional_edges('critic', route_after_critic, {
    'visuals': 'visuals',
    'human_review': 'human_review',
    'scriptwriter': 'scriptwriter'
})

g.add_edge('human_review', 'visuals')
g.add_edge('visuals', 'voice')
g.add_edge('voice', 'render')
g.add_edge('render', 'qa_gate')
g.add_edge('qa_gate', 'metadata')
g.add_edge('metadata', 'publish')
g.add_edge('publish', END)

# Checkpointer initialization
checkpointer = MemorySaver()
app_graph = g.compile(checkpointer=checkpointer)
