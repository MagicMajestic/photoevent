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

- June 28, 2025: Completed all fixes and created production deployment guide
  - ✅ Fixed statistics consistency between admin_profile and admin_stats dropdown interfaces
  - ✅ Fixed screenshot status display in profile dropdowns - now updates correctly after moderation
  - ✅ Fixed database insertion to properly set new screenshots as pending (NULL) not rejected (0)
  - ✅ Created comprehensive deployment guide for SparkedHost and other VPS providers
  - ✅ Fixed statistics calculation bug - now correctly handles database integer values (1/0) vs boolean (True/False)
  - ✅ Dropdown lists now properly display moderation status (✅2 ❌1 ⏳0) with real-time updates
  - ✅ Player profiles show accurate approved/rejected/pending counts across all interfaces
  - ✅ Players receive personal screenshot numbers (1st, 2nd, 3rd) instead of system IDs
  - ✅ Added pagination system for admin stats to handle 100+ participants
  - ✅ Each page shows 25 participants with navigation buttons and position indicators
  - ✅ System scales to unlimited number of participants with full production readiness

- June 28, 2025: Successfully migrated from Replit Agent to Replit environment
  - ✅ Fixed dependency conflicts between discord.py and py-cord
  - ✅ Bot connects successfully and runs without errors
  - ✅ Fixed notification system - players now receive actual DM messages
  - ✅ Removed incorrect $10,000 reward message from approvals
  - ✅ Enhanced button states to update properly after moderation actions
  - ✅ All core functionality working: registration, screenshot submission, admin moderation

- June 28, 2025: Fixed moderation system and enhanced notification features
  - ✅ Fixed screenshot status updates - now properly shows after moderation in profile
  - ✅ Added automatic user notifications for screenshot approval/rejection
  - ✅ Created reason input modal for screenshot rejection with custom messages
  - ✅ Fixed database queries to include is_approved field for accurate status display
  - ✅ Enhanced moderation interface with better feedback and button states
  - ✅ All status updates now work correctly across dropdown menus and detailed views

- June 28, 2025: Fixed all registration and moderation issues + enhanced admin features
  - ✅ Fixed registration modal - now works correctly after database reset
  - ✅ Enhanced player profiles with detailed screenshot breakdown (approved/rejected/pending)
  - ✅ Fixed screenshot status display in dropdown lists and detailed views
  - ✅ Enhanced /admin_disqualify with "cancel" option to restore players
  - ✅ Added automatic DM notifications for disqualification/restoration
  - ✅ Improved error handling for all user interactions
  - ✅ All interactive elements fully functional after fixes

- June 28, 2025: Fixed all reported issues and enhanced functionality
  - ✅ Fixed screenshot status display - now properly shows approved/rejected/pending
  - ✅ Replaced Discord IDs with @tags in all statistics and displays
  - ✅ Top players ranking now based on approved screenshots count (not total)
  - ✅ Removed "Active players" count from statistics (cleaner display)
  - ✅ Added /reset_stats command with confirmation dialog for new events
  - ✅ Enhanced leaderboard sorting: approved screenshots first, then total screenshots
  - ✅ All status updates work correctly after moderation actions

- June 28, 2025: Completed full bot implementation with advanced moderation features
  - ✅ Screenshot moderation system with approve/reject buttons
  - ✅ Enhanced /admin_stats with top players list and dropdown menu for selection
  - ✅ Player profiles show approved screenshot count and full dropdown list
  - ✅ /calculate command generates ready-to-use /givemoney commands
  - ✅ Database updated with is_approved field for screenshot approval tracking
  - ✅ Fixed command response issues and added proper error handling
  - ✅ All interactive elements working: dropdowns, buttons, modals

- June 28, 2025: Successfully implemented Discord bot with full functionality
  - ✅ Database layer with SQLite (players and submissions tables)
  - ✅ Player registration system using modal forms and buttons
  - ✅ Screenshot submission handling in DMs
  - ✅ Event time validation with timezone support
  - ✅ Admin commands for stats, player profiles, and disqualification
  - ✅ Bot successfully connects to Discord (running as Фотографер#3534)
  - ✅ Commands respond correctly with guild_ids configuration

- June 28, 2025: Converted to modern slash commands with enhanced features
  - ✅ All commands converted from prefix-based to slash commands
  - ✅ /start command now shows privately to user only
  - ✅ Enhanced /admin_stats with dropdown menu for player selection
  - ✅ Admin commands show user tags and StaticIDs instead of raw IDs
  - ✅ Removed admin role requirement - now uses Discord admin permissions
  - ✅ All admin commands are private and ephemeral

- June 28, 2025: Successfully migrated from Replit Agent to Replit environment
  - ✅ Resolved dependency conflicts between discord.py and py-cord
  - ✅ Fixed import and syntax issues for py-cord compatibility
  - ✅ Created working bot instance with proper environment setup
  - ✅ Bot connects successfully with BOT_TOKEN environment variable
  - ✅ Database initialization working correctly
  - ✅ Basic slash commands (/test, /start) are functional

## Current Status

✅ **Migration Complete!** The Discord bot has been successfully migrated to the Replit environment. The project structure, dependencies, and security configurations are properly set up.

**What's working:**
- Bot connects to Discord (running as Фотографер#3534)
- Database is initialized and working
- Basic bot framework is operational
- Environment variables are properly configured

**Next steps for development:**
1. Complete the full feature implementation (registration modals, admin commands)
2. Enable "Message Content Intent" in Discord Developer Portal for DM functionality
3. Configure GUILD_ID and ADMIN_ROLE_ID in config.py for your specific server
4. Test all functionality on your target Discord server

## Changelog

- June 27, 2025: Initial setup
- June 28, 2025: Complete bot implementation and successful deployment