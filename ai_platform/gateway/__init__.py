"""Shared, optional inference gateway. Core business workflows never depend on it."""

from ai_platform.gateway.service import AgentSpec, GatewayResult, ModelGateway, agents

__all__ = ["AgentSpec", "GatewayResult", "ModelGateway", "agents"]
