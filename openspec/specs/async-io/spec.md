# Spec: Async IO & Concurrency Rules

## Requirements

### Requirement: External APIs MUST NOT block the event loop
Any external SDK or network request executed within the pp/services/ layer MUST NOT block the FastAPI asyncio event loop.

#### Scenario: Native Async Client (Gemini / Google GenAI)
- **Given** an external SDK that provides a native asynchronous implementation (e.g., google-genai)
- **When** the SDK is invoked within an sync def method (e.g., CorrectionService, ExplanationService)
- **Then** the application MUST use the asynchronous interface (client.aio)
- **And** it must be waited, yielding execution to the event loop

#### Scenario: Synchronous SDKs (Resend)
- **Given** an external SDK that only provides a synchronous implementation relying on blocking IO (e.g., esend python SDK using equests)
- **When** the SDK is invoked within an sync def method (e.g., EmailService)
- **Then** the call MUST be wrapped using wait starlette.concurrency.run_in_threadpool(...)
- **And** the direct synchronous invocation MUST NOT be used on the main thread

#### Scenario: Blocking Monitor Test
- **Given** the test suite is running
- **When** ackend/tests/test_async_blocking.py executes
- **Then** a background task monitoring the event loop lag MUST report less than 50ms of delay
- **And** any blocking call simulating high latency MUST NOT increase this lag
