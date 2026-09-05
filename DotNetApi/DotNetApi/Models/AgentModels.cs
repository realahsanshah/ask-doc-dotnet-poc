using System.Text.Json.Serialization;

namespace DotNetApi.Models
{
    // What the client (browser / caller) sends us to ask a question.
    public class AskRequest
    {
        public string? Question { get; set; }
    }

    // A single piece of supporting evidence returned alongside the answer,
    // e.g. "Source: manual.pdf" and the relevant text snippet from it.
    public class SourceSnippet
    {
        public string Source { get; set; } = string.Empty;
        public string Snippet { get; set; } = string.Empty;
    }

    // What we send back to our own caller: the generated answer plus the
    // source snippets that were used to produce it.
    public class AskResponse
    {
        public string Answer { get; set; } = string.Empty;
        public List<SourceSnippet> SourceSnippets { get; set; } = [];
    }

    // ---------------------------------------------------------------------
    // The classes below exist only to talk to the Python service. Its JSON
    // uses snake_case field names ("source_snippets"), while our own C#
    // models above use PascalCase properties serialized as camelCase.
    // [JsonPropertyName] tells System.Text.Json exactly which JSON key to
    // read/write for each property, regardless of C# naming conventions.
    // ---------------------------------------------------------------------

    // Request body we POST to the Python service's /ask endpoint.
    public class PythonAskRequest
    {
        [JsonPropertyName("question")]
        public string Question { get; set; } = string.Empty;
    }

    // Mirrors a single snippet object as returned by the Python service.
    public class PythonSourceSnippet
    {
        [JsonPropertyName("source")]
        public string Source { get; set; } = string.Empty;

        [JsonPropertyName("snippet")]
        public string Snippet { get; set; } = string.Empty;
    }

    // Mirrors the full response body returned by the Python service.
    public class PythonAskResponse
    {
        [JsonPropertyName("answer")]
        public string Answer { get; set; } = string.Empty;

        [JsonPropertyName("source_snippets")]
        public List<PythonSourceSnippet> SourceSnippets { get; set; } = [];
    }
}
