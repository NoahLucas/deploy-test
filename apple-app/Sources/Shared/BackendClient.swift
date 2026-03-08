import Foundation

enum BackendError: LocalizedError {
    case invalidURL
    case server(String)
    case decoding

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid backend URL."
        case .server(let detail):
            return detail
        case .decoding:
            return "Failed to decode backend response."
        }
    }
}

final class BackendClient {
    static let shared = BackendClient()

    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    private init() {
        self.decoder = JSONDecoder()
        self.encoder = JSONEncoder()
    }

    private func makeURL(path: String) throws -> URL {
        guard let url = URL(string: path, relativeTo: SiteConfiguration.apiBaseURL) else {
            throw BackendError.invalidURL
        }
        return url
    }

    private func perform<T: Decodable>(
        method: String,
        path: String,
        adminToken: String? = nil,
        body: Data? = nil
    ) async throws -> T {
        let url = try makeURL(path: path)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = adminToken, !token.isEmpty {
            request.setValue(token, forHTTPHeaderField: "X-Admin-Token")
        }
        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw BackendError.server("Invalid response")
        }

        guard (200..<300).contains(http.statusCode) else {
            if let decoded = try? decoder.decode(APIErrorResponse.self, from: data) {
                throw BackendError.server(decoded.detail)
            }
            throw BackendError.server("Request failed with status \(http.statusCode)")
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw BackendError.decoding
        }
    }

    func listEndpointToggles(adminToken: String) async throws -> EndpointToggleListResponse {
        try await perform(method: "GET", path: "/api/v1/admin/endpoints", adminToken: adminToken)
    }

    func setEndpointToggle(path: String, enabled: Bool, adminToken: String) async throws -> EndpointToggleListResponse {
        let payload = EndpointToggleUpdateRequest(path: path, enabled: enabled)
        let body = try encoder.encode(payload)
        return try await perform(method: "POST", path: "/api/v1/admin/endpoints/toggle", adminToken: adminToken, body: body)
    }

    func generateDailyBrief(
        priorities: [String],
        risks: [String],
        context: String,
        adminToken: String
    ) async throws -> LabDailyBriefResponse {
        let payload = LabDailyBriefRequest(priorities: priorities, risks: risks, context: context)
        let body = try encoder.encode(payload)
        return try await perform(method: "POST", path: "/api/v1/lab/daily-brief", adminToken: adminToken, body: body)
    }

    func listSquarespaceEvents(adminToken: String) async throws -> SquarespaceEventsResponse {
        try await perform(method: "GET", path: "/api/v1/admin/squarespace/events", adminToken: adminToken)
    }
}
