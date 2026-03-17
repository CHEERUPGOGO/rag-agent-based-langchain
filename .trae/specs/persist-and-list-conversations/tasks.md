# Tasks

- [x] Task 1: Backend - Implement automatic title generation
  - [x] Update `CheckpointManager.add_message` in `backend/app/conversation/checkpoint_manager.py` to check if it's the first user message and update the `title` field in the `conversations` table.
- [x] Task 2: Frontend - Enhance User ID and List Management
  - [x] Modify `useChat.js` to return `userId` from the hook.
  - [x] Update `App.jsx` to use the `userId` from `useChat` when calling `loadConversations`.
  - [x] Ensure `loadConversations` is called when `userId` becomes available.
- [x] Task 3: Frontend - Improve Message Parsing
  - [x] Update `loadConversationHistory` in `useChat.js` to handle `tool` message types (map to appropriate role or display logic).
  - [x] Verify that `getConversationState` response format aligns with frontend parsing logic.

# Task Dependencies
- Task 2 depends on Task 1 (indirectly, for better UI experience with titles)
