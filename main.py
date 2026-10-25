
            elif message_type == "check_bingo" and game:
                is_bingo = game.check_bingo(int(user_id))
                await websocket.send_json({
                    "type": "bingo_result", "is_bingo": is_bingo, "user_id": user_id
                })
                if is_bingo:
                    game.status = "finished"
                    await broadcast_game_update(game_id)

            elif message_type == "request_update" and game:
                await websocket.send_json({
                    "type": "game_state",
                    "data": game.to_dict(),
                    "card": game.get_card_for_user(int(user_id)),
                    "marked": game.get_marked_for_user(int(user_id)),
                })

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"WebSocket error: {exc}")
    finally:
        connections = active_connections.get(game_id, {})
        connections.pop(user_id, None)
        if not connections:
            active_connections.pop(game_id, None)


async def broadcast_game_update(game_id: str):
    game = active_games.get(game_id)
    if not game:
        return
    for user_id, websocket in list(active_connections.get(game_id, {}).items()):
        try:
            await websocket.send_json({"type": "game_update", "data": game.to_dict()})
        except Exception:
            active_connections.get(game_id, {}).pop(user_id, None)


@app.get("/api/game/{game_id}")
async def get_game_state(game_id: str):
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.to_dict()


@app.get("/api/card/{game_id}/{user_id}")
async def get_user_card(game_id: str, user_id: int):
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    card = game.get_card_for_user(user_id)
    if not card:
        raise HTTPException(status_code=404, detail="User not in game")
    return {"card": card, "marked": game.get_marked_for_user(user_id)}


@app.post("/api/draw/{game_id}")
async def draw_number_api(game_id: str, admin_id: int):
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.admin_id != admin_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    number = game.draw_number()
    if number is None:
        game.status = "finished"
        return {"status": "finished", "message": "All numbers drawn"}
    await broadcast_game_update(game_id)
    return {"number": number, "total_called": len(game.called_numbers)}


@app.get("/")
async def root():
    return {
        "message": "🇪🇹 Habesha BINGO API",
        "bot": BOT_NAME,
        "username": BOT_USERNAME,
        "status": "running",
    }


# ===== RUN BOT =====

async def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Set it in Render Environment variables.")

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("draw", draw_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("contact", contact_command))

    print(f"🤖 {BOT_NAME} (@{BOT_USERNAME}) is starting...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()


if __name__ == "__main__":
    import threading

    def start_bot_thread():
        try:
            asyncio.run(run_bot())
        except Exception as exc:
            print(f"Telegram bot stopped: {exc}")

    threading.Thread(target=start_bot_thread, daemon=True).start()
    print(f"🚀 Habesha BINGO Server running on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
