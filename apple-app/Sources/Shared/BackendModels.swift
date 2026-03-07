import Foundation

struct EndpointToggleItem: Codable, Identifiable {
    var id: String { path }
    let path: String
    let platform: String
    var enabled: Bool
}

struct EndpointToggleListResponse: Codable {
    let items: [EndpointToggleItem]
}

struct EndpointToggleUpdateRequest: Codable {
    let path: String
    let enabled: Bool
}

struct LabDailyBriefRequest: Codable {
    let priorities: [String]
    let risks: [String]
    let context: String
}

struct LabDailyBriefResponse: Codable {
    let headline: String
    let topActions: [String]
    let watchouts: [String]
    let communicationDraft: String

    enum CodingKeys: String, CodingKey {
        case headline
        case topActions = "top_actions"
        case watchouts
        case communicationDraft = "communication_draft"
    }
}

struct SquarespaceEventItem: Codable, Identifiable {
    let id: Int
    let eventId: String
    let eventType: String
    let websiteId: String

    enum CodingKeys: String, CodingKey {
        case id
        case eventId = "event_id"
        case eventType = "event_type"
        case websiteId = "website_id"
    }
}

struct SquarespaceEventsResponse: Codable {
    let items: [SquarespaceEventItem]
}

struct APIErrorResponse: Codable {
    let detail: String
}
