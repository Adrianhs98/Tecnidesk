# SDD Specifications: async-io-refactor

## 1. File Modifications

### CorrectionService (ackend/app/services/correction_service.py)
- **Modification**: Update handle_chat_message to use the asynchronous client. Replace client.models.generate_content(...) with wait client.aio.models.generate_content(...). Ensure import google.genai configuration supports this.

### ExplanationService (ackend/app/services/explanation_service.py)
- **Modification**: Update generate_explanation to use the asynchronous client. Replace client.models.generate_content(...) with wait client.aio.models.generate_content(...).

### EmailService (ackend/app/services/email_service.py)
- **Modification**: Import un_in_threadpool from starlette.concurrency. Replace synchronous calls to esend.Emails.send(...) with wait run_in_threadpool(resend.Emails.send, ...) in all async methods.

## 2. Architecture of the Testing Safeguard

- **Target Location**: ackend/tests/test_async_blocking.py
- **Modification**: Create a new test file that ensures the event loop is not blocked by these services.
- **Approach**: 
  1. Implement an async generator/task monitor_loop_lag that continuously yields/sleeps for 10ms and measures the actual elapsed time.
  2. Start the monitor as a background task using syncio.create_task.
  3. Call the EmailService (using real resend call or a deliberately blocking mock if testing the safeguard, but since we test our application code, we mock esend.Emails.send using a mock that internally does a 	ime.sleep(1) to simulate sync block if we want to ensure threadpool usage, or simply assert it's called in threadpool).
  Wait, the most robust test is to patch esend.Emails.send with a function that runs 	ime.sleep(0.5). Then we call wait send_ticket_email(...). While it runs, the monitor_loop_lag runs. If send_ticket_email properly uses un_in_threadpool, the event loop lag will remain under 50ms. If someone removes un_in_threadpool in the future, the 	ime.sleep(0.5) will block the event loop, and the monitor lag will spike to 500ms, failing the test!
  4. Same test for CorrectionService using a mock for genai that sleeps for 0.5 seconds if called synchronously, or wait asyncio.sleep(0.5) if called asynchronously.

## 3. Risks & Considerations
- **Thread Pool Exhaustion**: High email load might stall threadpool requests. We assume low volume for this application.
