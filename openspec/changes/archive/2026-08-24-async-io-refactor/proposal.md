# SDD Proposal: async-io-refactor

## Business Problem
The application currently uses synchronous external API calls within asynchronous FastAPI endpoints. Specifically, `CorrectionService` and `ExplanationService` use the synchronous Gemini SDK (`client.models.generate_content`), and `EmailService` uses the synchronous Resend SDK (`resend.Emails.send()`). These synchronous calls block the FastAPI event loop, leading to 504 timeouts on the Render deployment platform (which are surfaced to the frontend as CORS errors). This results in a poor user experience and degrades the application's scalability and reliability.

## Target Users
- **End Users:** Will experience faster response times and reliable operation without timeouts or false CORS errors.
- **Developers/Maintainers:** Will benefit from a non-blocking asynchronous architecture and an automated test safeguard to prevent future blocking regressions.

## Business Rules
1. **Gemini SDK Refactor:** All interactions with the Gemini API within `CorrectionService` and `ExplanationService` must be refactored to use the asynchronous client (`client.aio.models.generate_content`).
2. **Resend SDK Refactor:** Since the Resend Python SDK is synchronous (relying on the `requests` library), calls to `resend.Emails.send()` within `EmailService` must be offloaded to a thread pool using `starlette.concurrency.run_in_threadpool` to prevent blocking the event loop.
3. **Architectural Safeguard:** A dedicated test suite must be implemented to verify that core service methods (e.g., `CorrectionService.handle_chat_message`, `ExplanationService.generate_explanation`) do not block the asyncio event loop for more than 50 milliseconds. This ensures regressions are caught early.

## Product Outcome
- Resolution of 504 Gateway Timeouts and apparent CORS errors on Render.
- Fully non-blocking event loop across the application.
- Increased throughput and responsiveness for generative AI and email sending endpoints.
- Automated testing infrastructure to monitor and enforce event loop responsiveness.

## Edge Cases
- **Thread Pool Exhaustion:** When offloading Resend calls, extreme bursts of email requests might exhaust the thread pool. The system should gracefully queue or handle these requests.
- **Mocking Asynchronous Clients:** The new test safeguard must accurately mock the asynchronous Gemini client and thread pool execution without artificially hiding blocking behavior.
- **Network Latency:** The event loop responsiveness test must focus solely on CPU blocking (event loop starvation), not network latency, meaning IO operations should be properly mocked or awaited.

## Non-goals
- Replacing the Resend SDK with a different email provider.
- Implementing a full background job queue (e.g., Celery or RedisQ) for email sending; offloading to a thread pool is sufficient for the current scope.
- Refactoring the entire application architecture outside of the specified services (CorrectionService, ExplanationService, EmailService).
