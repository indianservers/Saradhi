# Merchant connectivity and recovery

The KDS refreshes tasks and stations every 10 seconds, supports pull-to-refresh, and retains the last rendered task list while showing a disconnected state after a failed request. Reconnection reloads server-authoritative task state. Task mutations use expected versions, so stale devices cannot silently overwrite a newer state. Permitted repeated transition requests return the current state.

The app does not queue order acceptance or task commands offline. It does not provide push-notification recovery, durable event deduplication on devices, or offline order intake. A failed update should be retried only after the app reloads the server state; the UI does not promise delivery when disconnected.
