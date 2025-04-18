import Cocoa
import Foundation

class ResumeAutoFillService: NSObject {
    @objc func runService(pboard: NSPasteboard, userData: String, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        guard let selectedText = pboard.string(forType: .string) else {
            print("No text selected")
            return
        }
        
        // Get the current application and focused element
        let appInfo = getFrontmostAppInfo()
        let elementInfo = getFocusedElementInfo()
        
        // Prepare context data for LLM
        let contextData: [String: Any] = [
            "selectedText": selectedText,
            "appName": appInfo?["name"] as? String ?? "Unknown",
            "windowTitle": elementInfo["windowTitle"] as? String ?? "Unknown",
            "fieldLabel": elementInfo["title"] as? String ?? elementInfo["placeholder"] as? String ?? "Unknown",
            "fieldRole": elementInfo["role"] as? String ?? "Unknown",
            "surroundingText": elementInfo["surroundingText"] as? String ?? ""
        ]
        
        // Call Python script for LLM processing
        callPythonScript(with: contextData) { result in
            if let resultText = result {
                // Insert the text at the current cursor position
                self.insertTextAtCursor(resultText)
            }
        }
    }
    
    private func getFrontmostAppInfo() -> [String: Any]? {
        let workspace = NSWorkspace.shared
        guard let frontmostApp = workspace.frontmostApplication else {
            return nil
        }
        
        return [
            "name": frontmostApp.localizedName ?? "Unknown",
            "bundleId": frontmostApp.bundleIdentifier ?? "Unknown",
            "processId": frontmostApp.processIdentifier
        ]
    }
    
    private func getFocusedElementInfo() -> [String: Any] {
        // This would use the Accessibility API to get information about the focused element
        // For now, returning a placeholder - this would be implemented using AXUIElementRef
        return [
            "role": "textField",
            "title": "Unknown",
            "placeholder": "Unknown",
            "windowTitle": "Unknown",
            "surroundingText": ""
        ]
    }
    
    private func callPythonScript(with context: [String: Any], completion: @escaping (String?) -> Void) {
        // Convert context to JSON
        guard let jsonData = try? JSONSerialization.data(withJSONObject: context),
              let jsonString = String(data: jsonData, encoding: .utf8) else {
            completion(nil)
            return
        }
        
        // Path to the Python script
        let scriptPath = Bundle.main.path(forResource: "autofill_bridge", ofType: "py")!
        
        // Create a process to run the Python script
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        task.arguments = [scriptPath, jsonString]
        
        let outputPipe = Pipe()
        task.standardOutput = outputPipe
        
        do {
            try task.run()
            
            let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
            if let output = String(data: outputData, encoding: .utf8) {
                completion(output.trimmingCharacters(in: .whitespacesAndNewlines))
            } else {
                completion(nil)
            }
        } catch {
            print("Error running Python script: \(error)")
            completion(nil)
        }
    }
    
    private func insertTextAtCursor(_ text: String) {
        // This would use the Accessibility API to insert text at the current cursor position
        // For now, we'll simulate it with keyboard events
        
        // Create a CGEvent for each character
        for char in text {
            // This is a simplified approach - a real implementation would handle special characters
            // and use proper key codes
            let keyCode: CGKeyCode = 0 // Placeholder
            
            let keyDownEvent = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: true)
            keyDownEvent?.flags = .maskNonCoalesced
            keyDownEvent?.post(tap: .cghidEventTap)
            
            let keyUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: false)
            keyUpEvent?.flags = .maskNonCoalesced
            keyUpEvent?.post(tap: .cghidEventTap)
        }
    }
}
