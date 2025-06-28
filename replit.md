# Discord Event Bot

## Overview

This is a Discord bot designed to manage events with player registration and screenshot submissions. The bot allows players to register for events and submit screenshots during active event periods. It includes administrative features for managing participants and event status.

## System Architecture

The application follows a modular architecture with three main components:
- **main.py**: Core bot logic and Discord integration
- **database.py**: Data persistence layer using SQLite
- **config.py**: Configuration management and environment variables

The architecture is designed for simplicity and maintainability, using Discord.py library for bot functionality and SQLite for local data storage.

## Key Components

### Bot Framework
- **Technology**: Discord.py (Pycord variant)
- **Intents**: Configured for message content and DM access
- **Event Management**: Time-based event activation using ISO 8601 timestamps

### Database Layer
- **Technology**: SQLite3 with direct SQL queries
- **Tables**: 
  - `players`: Stores player registration data (discord_id, static_id, nickname, registration_time, is_disqualified)
  - `submissions`: Tracks screenshot submissions (submission_id, player_id, screenshot_url, submission_time, is_valid)
- **Design**: Simple relational model with foreign key relationships

### Configuration Management
- **Environment Variables**: Bot token loaded from environment
- **Hardcoded IDs**: Guild and admin role IDs configured in config.py
- **Event Timing**: ISO 8601 formatted timestamps for event start/end
- **Visual Theme**: Raspberry color scheme for embed messages

## Data Flow

1. **Player Registration**: Users provide static_id and nickname → stored in players table
2. **Event Validation**: Bot checks current time against configured event window
3. **Screenshot Submission**: Players submit images during active events → stored in submissions table
4. **Administrative Actions**: Admins can manage player status and submissions

## External Dependencies

- **discord.py**: Primary bot framework
- **python-dotenv**: Environment variable management
- **pytz**: Timezone handling for event scheduling
- **sqlite3**: Built-in Python database functionality

## Deployment Strategy

The application is designed for simple deployment:
- Single bot instance architecture
- Local SQLite database (no external database required)
- Environment variable configuration for sensitive data
- Timezone-aware event management

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- June 28, 2025: Successfully implemented Discord bot with full functionality
  - ✅ Database layer with SQLite (players and submissions tables)
  - ✅ Player registration system using modal forms and buttons
  - ✅ Screenshot submission handling in DMs
  - ✅ Event time validation with timezone support
  - ✅ Admin commands for stats, player profiles, and disqualification
  - ✅ Bot successfully connects to Discord (running as Фотографер#3534)
  - ⚠️ Needs Message Content Intent enabled for full DM functionality
  - ⚠️ Requires Guild ID and Admin Role ID configuration

## Current Status

The bot is running and connected to Discord. Next steps:
1. Enable "Message Content Intent" in Discord Developer Portal
2. Configure GUILD_ID and ADMIN_ROLE_ID in config.py
3. Test all functionality on target Discord server

## Changelog

- June 27, 2025: Initial setup
- June 28, 2025: Complete bot implementation and successful deployment