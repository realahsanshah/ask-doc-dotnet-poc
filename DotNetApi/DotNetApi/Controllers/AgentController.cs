using System.Net.Http.Json;
using DotNetApi.Models;
using Microsoft.AspNetCore.Mvc;

namespace DotNetApi.Controllers
{
    [ApiController]
    [Route("api/agent")]
    public class AgentController : ControllerBase
    {
        // The name we registered this HttpClient under in Program.cs via
        // builder.Services.AddHttpClient("PythonAgent", ...). Using a named
        // client (instead of "new HttpClient()") lets the framework manage
        // connection pooling and lets us configure its BaseAddress in one place.
        private const string PythonAgentClientName = "PythonAgent";

        private readonly IHttpClientFactory _httpClientFactory;

        // Constructor (dependency injection): ASP.NET Core sees this controller
        // needs an IHttpClientFactory and automatically supplies one, because
        // it was registered in Program.cs (AddHttpClient registers the factory too).
        public AgentController(IHttpClientFactory httpClientFactory)
        {
            _httpClientFactory = httpClientFactory;
        }

        // POST api/agent/ask
        // Accepts a question, forwards it to the Python service, and returns
        // the answer + supporting source snippets.
        [HttpPost("ask")]
        public async Task<ActionResult<AskResponse>> Ask([FromBody] AskRequest request)
        {
            // Validate input before doing any network work.
            if (string.IsNullOrWhiteSpace(request.Question))
            {
                return BadRequest(new { error = "Question must not be null or empty." });
            }

            // Get (or create) the named HttpClient configured in Program.cs.
            var client = _httpClientFactory.CreateClient(PythonAgentClientName);

            var pythonRequest = new PythonAskRequest { Question = request.Question };

            try
            {
                // PostAsJsonAsync serializes pythonRequest to JSON and sends it
                // as the request body. "await" means we don't block the current
                // thread while waiting for the network call to complete.
                var httpResponse = await client.PostAsJsonAsync("/ask", pythonRequest);

                // EnsureSuccessStatusCode throws an HttpRequestException if the
                // Python service responded with a non-2xx status code (e.g. 500).
                // We catch that below and turn it into a clean 502 response.
                httpResponse.EnsureSuccessStatusCode();

                var pythonResponse = await httpResponse.Content.ReadFromJsonAsync<PythonAskResponse>();

                if (pythonResponse is null)
                {
                    return StatusCode(StatusCodes.Status502BadGateway,
                        new { error = "The agent service returned an empty or unreadable response." });
                }

                // Map the Python service's model onto our own public API model.
                var response = new AskResponse
                {
                    Answer = pythonResponse.Answer,
                    SourceSnippets = pythonResponse.SourceSnippets
                        .Select(s => new SourceSnippet { Source = s.Source, Snippet = s.Snippet })
                        .ToList()
                };

                return Ok(response);
            }
            catch (HttpRequestException ex)
            {
                // Thrown for connection failures (e.g. connection refused because
                // the Python service isn't running) or non-2xx status codes from
                // EnsureSuccessStatusCode above.
                return StatusCode(StatusCodes.Status502BadGateway,
                    new { error = $"Failed to reach the agent service: {ex.Message}" });
            }
            catch (TaskCanceledException ex)
            {
                // Thrown when the HttpClient's request times out.
                return StatusCode(StatusCodes.Status502BadGateway,
                    new { error = $"The agent service did not respond in time: {ex.Message}" });
            }
        }
    }
}
