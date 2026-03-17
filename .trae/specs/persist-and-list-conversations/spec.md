# Persist and List Conversations Spec

## Why
Users need to persist conversation history across service restarts and easily switch between different conversation threads in the UI. Currently, conversations are persisted in the backend, but the frontend integration for listing, switching, and generating meaningful titles is incomplete or needs optimization.

## What Changes
### Backend
- **Update Title Logic**: Automatically generate a conversation title based on the first user message in `CheckpointManager`.
- **API Consistency**: Ensure `list_conversations` correctly filters by `user_id`.

### Frontend
- **User ID Management**: Expose `userId` from `useChat` hook to allow `App` component to fetch user-specific conversations.
- **Conversation List**: Update `App.jsx` to pass `userId` when calling `getConversations`.
- **Message Parsing**: Enhance `loadConversationHistory` in `useChat.js` to robustly parse LangChain message types (Human, AI, System, Tool) from the backend state.

## Impact
- **Affected Specs**: None.
- **Affected Code**:
  - `backend/app/conversation/checkpoint_manager.py`
  - `frontend/src/hooks/useChat.js`
  - `frontend/src/App.jsx`

## ADDED Requirements
### Requirement: Automatic Title Generation
The system SHALL automatically update the conversation title to the first 30 characters of the first user message.

#### Scenario: First Message
- **WHEN** a user sends the first message in a new conversation
- **THEN** the conversation title in the database is updated to match the message content (truncated).

### Requirement: Persistent Conversation List
The system SHALL display a list of historical conversations on the sidebar, filtered by the current user.

#### Scenario: Service Restart
- **WHEN** the backend service is restarted and the user refreshes the page
- **THEN** the sidebar still displays the previous conversation history.

## MODIFIED Requirements
### Requirement: Message Parsing
**Existing**: Basic parsing of `human` and `ai` types.
**Modified**: Support `tool` message types and ensure robust JSON parsing for persisted states.
