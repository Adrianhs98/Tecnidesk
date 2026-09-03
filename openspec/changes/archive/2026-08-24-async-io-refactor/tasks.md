# Implementation Tasks: async-io-refactor

## PR 1: Core Async IO Refactoring
- [ ] **Task 1: Gemini Async Client Refactor** 
  - Update `CorrectionService` (`backend/app/services/correction_service.py`) to use `await client.aio.models.generate_content(...)`.
  - Update `ExplanationService` (`backend/app/services/explanation_service.py`) to use `await client.aio.models.generate_content(...)`.
- [ ] **Task 2: Resend Threadpool Refactor** 
  - Update `EmailService` (`backend/app/services/email_service.py`) to import `run_in_threadpool` from `starlette.concurrency`.
  - Wrap all synchronous `resend.Emails.send(...)` calls inside `await run_in_threadpool(...)`.

## PR 2: Testing Safeguards
- [ ] **Task 3: Async Event Loop Safeguard Test** 
  - Create `backend/tests/test_async_blocking.py`.
  - Implement a `monitor_loop_lag` background task that continuously sleeps for 10ms and measures elapsed time.
  - Patch the Resend and Gemini clients with mocks that perform a synchronous `time.sleep(0.5)`.
  - Assert that calling `EmailService` and `CorrectionService`/`ExplanationService` methods does not cause the event loop lag to exceed 50ms, thus ensuring threadpool and async clients are properly utilized.

## Review Workload Forecast
Chained PRs recommended: Yes
400-line budget risk: Low (Changes are localized refactoring of API calls and one new test file).
