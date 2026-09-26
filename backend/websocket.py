from fastapi import WebSocket, WebSocketDisconnect

from ai.assistant import analyze_message

from database.database import (
    initialize_database,
    create_meeting,
    add_user,
    save_message
)


initialize_database()

active_meeting_id = create_meeting(
    "AI Meeting Assistant"
)


connected_users = {}
meeting_messages = []


async def broadcast(message):

    for user in connected_users.values():

        await user["socket"].send_json(message)


async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    username = await websocket.receive_text()

    user_id = add_user(
        active_meeting_id,
        username
    )

    connected_users[username] = {
        "socket": websocket
    }

    await broadcast({
        "type": "join",
        "username": username,
        "message": f"{username} joined the meeting",
        "online_users": len(connected_users)
    })

    try:

        while True:

            message = await websocket.receive_text()

            meeting_messages.append({
                "username": username,
                "message": message
            })

            save_message(
                active_meeting_id,
                user_id,
                message
            )

            await broadcast({
                "type": "message",
                "username": username,
                "message": message
            })

            try:

                ai_result = analyze_message(message)

                await websocket.send_json({
                    "type": "ai_suggestion",
                    "suggestion": ai_result["suggestion"],
                    "topic": ai_result["topic"],
                    "is_question": ai_result["is_question"]
                })

            except Exception as error:

                print("AI error:", error)

                await websocket.send_json({
                    "type": "ai_suggestion",
                    "suggestion": (
                    "AI is temporarily unavailable. "
                    "Your message was saved successfully."
                ),
                "topic": "General Discussion",
                "is_question": False
            })

    except WebSocketDisconnect:

        print(f"{username} left the meeting")

    except Exception as error:

        print("WebSocket error:", error)

    finally:

        if username in connected_users:

            del connected_users[username]

            await broadcast({
                "type": "leave",
                "username": username,
                "message": f"{username} left the meeting",
                "online_users": len(connected_users)
            })