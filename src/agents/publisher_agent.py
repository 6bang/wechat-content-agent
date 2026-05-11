from __future__ import annotations

from dataclasses import dataclass

from agents.operations_agent import OperationsAgent
from models.content import ContentTopic, PublishPackage, ReviewResult


@dataclass
class PublisherAgent(OperationsAgent):
    def build_package(self, topic: ContentTopic, review: ReviewResult) -> PublishPackage:
        return self.build_publish_package(topic, review)
