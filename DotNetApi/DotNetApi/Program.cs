var builder = WebApplication.CreateBuilder(args);

// Add services to the container.

builder.Services.AddControllers();
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

// Register a named HttpClient dedicated to talking to the Python agent
// service. Naming it "PythonAgent" lets AgentController ask the injected
// IHttpClientFactory for this specific, pre-configured client via
// CreateClient("PythonAgent"), instead of constructing a raw HttpClient
// itself (which would bypass connection pooling and configuration).
builder.Services.AddHttpClient("PythonAgent", (serviceProvider, client) =>
{
    // Read the base URL from configuration (appsettings.json) rather than
    // hardcoding it, so it can differ between environments without a
    // code change.
    var configuration = serviceProvider.GetRequiredService<IConfiguration>();
    var baseUrl = configuration["PythonAgentSettings:BaseUrl"]
        ?? throw new InvalidOperationException(
            "Configuration value 'PythonAgentSettings:BaseUrl' is missing.");

    client.BaseAddress = new Uri(baseUrl);
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseDefaultFiles();
app.UseStaticFiles();


app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();
