using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
namespace Phlakalizer
{
    public class CuckooIOCGetter
    {
        private static readonly string ApiKey = "dd401e188b8d9e8c7a26416e92a2c2820cfe3591"; // Replace with your actual API key if needed
        private static readonly string AnalysesUrl = "http://192.168.16.154:8090/analyses/";
        private static readonly string AnalysisReportUrlBase = "http://192.168.16.154:8090/analysis/";
        private static readonly string TaskPostUrlBase = "http://192.168.16.154:8090/analysis/";

        private static readonly HttpClient Client = new HttpClient();

        public async void Getter(string tItem = null)
        {
            Client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("token", ApiKey);
            Client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

            try
            {
                // Fetch analyses list
                var responseAnalysesList = await Client.GetStringAsync(AnalysesUrl);
                var analysesData = JsonSerializer.Deserialize<AnalysesResponse>(responseAnalysesList);

                var finishedAnalyses = new Dictionary<string, FinishedAnalysis>();

                if (analysesData != null)
                {
                    foreach (var analysis in analysesData.Analyses)
                    {
                        if (analysis.State == "finished")
                        {
                            string targetItem = analysis.Target?.TargetName;
                            DateTime createdOn = analysis.CreatedOn;

                            if (!string.IsNullOrEmpty(targetItem) && (tItem != null && tItem.Equals(targetItem)))
                            {
                                if (!finishedAnalyses.ContainsKey(targetItem) ||
                                    createdOn > finishedAnalyses[targetItem].CreatedOn)
                                {
                                    finishedAnalyses[targetItem] = new FinishedAnalysis
                                    {
                                        Id = analysis.Id,
                                        CreatedOn = createdOn,
                                        TargetItem = targetItem
                                    };
                                }
                            }
                        }
                    }

                    foreach (var finishedAnalysis in finishedAnalyses.Values)
                    {
                        var analysisReportUrl = $"{AnalysisReportUrlBase}{finishedAnalysis.Id}";
                        var responseAnalysisReport = await Client.GetStringAsync(analysisReportUrl);
                        var analysisReportData = JsonSerializer.Deserialize<AnalysisReport>(responseAnalysisReport);

                        if (analysisReportData != null)
                        {
                            string sanitizedFileName = GetSanitizedFileName(finishedAnalysis.TargetItem);
                            string outputFilePath = $"{sanitizedFileName}.txt";

                            using (var writer = new StreamWriter(outputFilePath))
                            {
                                foreach (var task in analysisReportData.Tasks)
                                {
                                    if (task.Id != null)
                                    {
                                        var taskPostUrl = $"{TaskPostUrlBase}{finishedAnalysis.Id}/task/{task.Id}/post";

                                        try
                                        {
                                            var payload = JsonSerializer.Serialize(new
                                            {
                                                settings = new
                                                {
                                                    dump_memory = false,
                                                    platforms = new[]
                                                    {
                                                        new { os_version = "10", tags = new string[0], platform = "windows" }
                                                    },
                                                    enforce_timeout = true,
                                                    options = new { },
                                                    manual = true,
                                                    timeout = 300,
                                                    machines = new string[0],
                                                    priority = 1,
                                                    extrpath = new string[0]
                                                },
                                                state = "finished"
                                            });

                                            var postResponse = await Client.PostAsync(taskPostUrl, new StringContent(payload, Encoding.UTF8, "application/json"));
                                            postResponse.EnsureSuccessStatusCode();

                                            var responseContent = await postResponse.Content.ReadAsStringAsync();
                                            await writer.WriteLineAsync($"Task ID: {task.Id}");
                                            await writer.WriteLineAsync(responseContent);
                                            await writer.WriteLineAsync("--------------------");
                                        }
                                        catch (Exception ex)
                                        {
                                            await writer.WriteLineAsync($"Task ID: {task.Id} - Error");
                                            await writer.WriteLineAsync($"Error: {ex.Message}");
                                            await writer.WriteLineAsync("--------------------");
                                        }
                                    }
                                }
                            }

                            Console.WriteLine($"Output for analysis ID: {finishedAnalysis.Id} saved to: {outputFilePath}");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"An error occurred: {ex.Message}");
            }
        }

        private static string GetSanitizedFileName(string input) =>
            string.Concat(input.Split(Path.GetInvalidFileNameChars()));

        // Models for JSON Deserialization
        public class AnalysesResponse
        {
            public List<Analysis> Analyses { get; set; }
        }

        public class Analysis
        {
            public string Id { get; set; }
            public string State { get; set; }
            public Target Target { get; set; }
            public DateTime CreatedOn { get; set; }
        }

        public class Target
        {
            [JsonPropertyName("target")]
            public string TargetName { get; set; }
        }

        public class FinishedAnalysis
        {
            public string Id { get; set; }
            public DateTime CreatedOn { get; set; }
            public string TargetItem { get; set; }
        }

        public class AnalysisReport
        {
            public List<Task> Tasks { get; set; }
        }

        public class Task
        {
            public string Id { get; set; }
        }
    }
}