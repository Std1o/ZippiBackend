from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json
import asyncio

from ..service.orders import OrderService
from ..service.websocket_manager import manager
from ..database import get_session

router = APIRouter(tags=['WebSocket'])


@router.websocket("/ws/orders/{order_number}")
async def websocket_order(
        websocket: WebSocket,
        order_number: str
):
    """
    WebSocket соединение для отслеживания статуса заказа.
    Возвращает только сущность order при каждом обновлении.
    """
    db = None

    try:
        # Принимаем соединение
        await websocket.accept()

        # Создаём сессию БД
        db = next(get_session())

        # Получаем заказ
        order_service = OrderService(db)
        order = order_service.get_order_by_number(order_number)

        if not order:
            await websocket.send_json({
                "error": "Заказ не найден"
            })
            await websocket.close(code=1008, reason="Order not found")
            return

        # Подключаем клиента
        if order_number not in manager.active_connections:
            manager.active_connections[order_number] = set()
        manager.active_connections[order_number].add(websocket)

        # Отправляем текущий заказ
        await websocket.send_json(order.model_dump(mode='json'))

        # Ожидаем сообщения (пинг-понг для поддержания соединения)
        while True:
            try:
                # Устанавливаем таймаут для получения сообщения
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Обрабатываем пинг
                if data == "ping":
                    await websocket.send_text("pong")
                elif data:
                    try:
                        msg = json.loads(data)
                        if msg.get('type') == 'ping':
                            await websocket.send_json({"type": "pong"})
                    except:
                        pass

            except asyncio.TimeoutError:
                # Отправляем пинг для проверки соединения
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "error": str(e)
            })
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
    finally:
        # Отключаем клиента
        if order_number in manager.active_connections:
            manager.active_connections[order_number].discard(websocket)
            if not manager.active_connections[order_number]:
                del manager.active_connections[order_number]

        if db:
            db.close()