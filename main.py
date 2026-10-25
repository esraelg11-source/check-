Skip to content
esraelg11-source
check-
Repository navigation
Code
Issues
Pull requests
Agents
Actions
Projects
Wiki
Security and quality
1
 (1)
Insights
Settings
Open a pull request
The change you just made was written to a new branch named esraelg11-source-patch-2. Create a pull request below to propose these changes. Learn more about diff comparisons here.
...
 Able to merge. These branches can be automatically merged.
@esraelg11-source
Add a title
*
Refactor Habesha BINGO bot and add contact command

Add a description
Comment
Updated the Habesha BINGO bot with improved environment variable handling, added a contact command, and refined the game logic.
Remember, contributions to this repository should follow our GitHub Community Guidelines.
️
Reviewers
No reviews
Assignees
No one—
Labels
None yet
Projects
None yet
Milestone
No milestone
Development
Use Closing keywords in the description to automatically close issues

Helpful resources
GitHub Community Guidelines
 1 commit
 1 file changed
 1 contributor
Commits on Oct 26, 2026
Refactor Habesha BINGO bot and add contact command 

@esraelg11-source
esraelg11-source authored now
 Showing  with 25 additions and 13 deletions.
  38 changes: 25 additions & 13 deletions38  
main.py
Original file line number	Diff line number	Diff line change
@@ -16,11 +16,11 @@
# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '8600848383:AAESb3yH5m2Gd_J9kL0Brw0uO1-6cbnBaeM')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-frontend-url.com')
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://habeshabingo.tail1a2d47.ts.net/')
PORT = int(os.getenv('PORT', 8000))
BOT_NAME = os.getenv('BOT_NAME', 'Habesha BINGO')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'HabeshaBingo_01Bot')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'BingoHabeshaGameBot')

# ===== GAME STATE =====
active_games = {}
@@ -219,18 +219,27 @@ async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    """Show commands and the official Habesha Bingo group."""
    await update.message.reply_text(
        f"🇪🇹 **ሐበሻ ቢንጎ / Habesha BINGO**\n"
        f"🤖 @{BOT_USERNAME}\n\n"
        f"📌 **ትዕዛዞች / Commands:**\n"
        f"• `/start` - ጨዋታ ጀምር / Start game\n"
        f"• `/draw` - ቁጥር ጥራ / Draw number (Admin only)\n"
        f"• `/status` - ሁኔታ ተመልከት / Check status\n"
        f"• `/help` - ይህን መልእክት አሳይ / Show this\n\n"
        f"🎯 ካርድህን ለማየት 'Open Card' ቁልፉን ተጫን\n\n"
        f"📞 እርዳታ ካስፈለገ: @HabeshBingoSupport\n"
        f"☎️ 0973240429 / 0941489662",
        f"📌 **Commands:**\n"
        f"• `/start` - Open Habesha Bingo\n"
        f"• `/draw` - Draw a number (admin only)\n"
        f"• `/status` - Check game status\n"
        f"• `/help` - Show this help\n"
        f"• `/contact` - Contact our agents\n\n"
        f"👥 Official group: https://t.me/HabeshaBingoOfficial\n"
        f"📞 Agent: @HabeshaBingo251",
        parse_mode='Markdown'
    )

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the official Habesha Bingo agent contact."""
    await update.message.reply_text(
        "🇪🇹 **Habesha Bingo — Contact Agents**\n\n"
        "📞 Agent: @HabeshaBingo251\n"
        "👥 Official group: https://t.me/HabeshaBingoOfficial",
        parse_mode='Markdown'
    )

@@ -404,12 +413,15 @@ async def root():
# ===== RUN BOT =====

async def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Set it in the Render Environment variables.")
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("draw", draw_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("contact", contact_command))

    print(f"🤖 {BOT_NAME} (@{BOT_USERNAME}) is running...")
    await application.initialize()
@@ -425,4 +437,4 @@ async def run_bot():
    bot_thread.start()

    print(f"🚀 Habesha BINGO Server running on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
Footer
© 2026 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Community
Docs
Contact
Manage cookies
Do not share my personal information
