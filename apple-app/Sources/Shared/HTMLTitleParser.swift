import Foundation

enum HTMLTitleParser {
    static func extractTitle(from html: String) -> String? {
        let pattern = "(?is)<title[^>]*>\\s*(.*?)\\s*</title>"
        guard let regex = try? NSRegularExpression(pattern: pattern) else {
            return nil
        }

        let range = NSRange(html.startIndex..<html.endIndex, in: html)
        guard let match = regex.firstMatch(in: html, options: [], range: range) else {
            return nil
        }

        guard let titleRange = Range(match.range(at: 1), in: html) else {
            return nil
        }

        return html[titleRange].trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
