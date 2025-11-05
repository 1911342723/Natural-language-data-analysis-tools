"""
Multi-Agent科学家团队系统
"""

from multi_agent.base_agent import BaseAgent, AgentMessage
from multi_agent.message_broker import MessageBroker
from multi_agent.pi_agent import PIAgent
from multi_agent.data_scientist_agent import DataScientistAgent
from multi_agent.statistician_agent import StatisticianAgent
from multi_agent.visualizer_agent import VisualizerAgent
from multi_agent.writer_agent import WriterAgent
from multi_agent.reviewer_agent import ReviewerAgent

__all__ = [
    'BaseAgent',
    'AgentMessage',
    'MessageBroker',
    'PIAgent',
    'DataScientistAgent',
    'StatisticianAgent',
    'VisualizerAgent',
    'WriterAgent',
    'ReviewerAgent',
]

