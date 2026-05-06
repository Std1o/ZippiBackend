from typing import Dict, Set
from fastapi import WebSocket
import json
from datetime import datetime


class ConnectionManager:
    """Менеджер для управления WebSocket соединениями"""

    def __init__(self):
        # Активные соединения: {order_number: {websocket}}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def send_order_update(self, order_number: str, order_data: dict):
        """Отправка обновления по конкретному заказу (только сущность order)"""
        if order_number in self.active_connections:
            # Отправляем только данные заказа, без обёртки
            message = json.dumps(order_data)

            connections = list(self.active_connections[order_number])
            for connection in connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass


# Глобальный экземпляр менеджера
manager = ConnectionManager()