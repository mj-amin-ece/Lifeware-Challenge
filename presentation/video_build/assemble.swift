import AVFoundation
import AppKit

struct Slide: Decodable { let image: String; let start: Double; let duration: Double; let audio: String; let offset: Double }
struct Timeline: Decodable { let total: Double; let slides: [Slide] }

let dir = CommandLine.arguments[1], out = CommandLine.arguments[2]
let tl = try! JSONDecoder().decode(Timeline.self, from: Data(contentsOf: URL(fileURLWithPath: dir + "/timeline.json")))
let W = 1920, H = 1080, scale: CMTimeScale = 600
func t(_ s: Double) -> CMTime { CMTime(value: CMTimeValue((s * Double(scale)).rounded()), timescale: scale) }

func pixelBuffer(_ path: String) -> CVPixelBuffer {
    let img = NSImage(contentsOfFile: path)!
    var rect = CGRect(x: 0, y: 0, width: W, height: H)
    let cg = img.cgImage(forProposedRect: &rect, context: nil, hints: nil)!
    var pb: CVPixelBuffer?
    CVPixelBufferCreate(nil, W, H, kCVPixelFormatType_32ARGB, [kCVPixelBufferCGImageCompatibilityKey: true, kCVPixelBufferCGBitmapContextCompatibilityKey: true] as CFDictionary, &pb)
    CVPixelBufferLockBaseAddress(pb!, [])
    let ctx = CGContext(data: CVPixelBufferGetBaseAddress(pb!), width: W, height: H, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pb!),
                        space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue)!
    ctx.draw(cg, in: CGRect(x: 0, y: 0, width: W, height: H))
    CVPixelBufferUnlockBaseAddress(pb!, [])
    return pb!
}

// 1. silent video: each slide held for its duration (a frame every 0.5 s keeps players and seeking happy)
let videoURL = URL(fileURLWithPath: dir + "/video_only.mov")
try? FileManager.default.removeItem(at: videoURL)
let writer = try! AVAssetWriter(outputURL: videoURL, fileType: .mov)
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: W, AVVideoHeightKey: H])
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: nil)
writer.add(input)
writer.startWriting()
writer.startSession(atSourceTime: .zero)
for s in tl.slides {
    let pb = pixelBuffer(dir + "/" + s.image)
    var time = s.start
    while time < s.start + s.duration - 1e-6 {
        while !input.isReadyForMoreMediaData { Thread.sleep(forTimeInterval: 0.01) }
        adaptor.append(pb, withPresentationTime: t(time))
        time += 0.5
    }
}
input.markAsFinished()
writer.endSession(atSourceTime: t(tl.total))
let done = DispatchSemaphore(value: 0)
writer.finishWriting { done.signal() }
done.wait()

// 2. composition: the video for exactly `total` seconds, each voice clip at its slide's start + lead-in
let comp = AVMutableComposition()
let vAsset = AVURLAsset(url: videoURL)
let vTrack = comp.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid)!
try! vTrack.insertTimeRange(CMTimeRange(start: .zero, duration: t(tl.total)), of: vAsset.tracks(withMediaType: .video)[0], at: .zero)
let aTrack = comp.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)!
for s in tl.slides {
    let a = AVURLAsset(url: URL(fileURLWithPath: dir + "/" + s.audio))
    let track = a.tracks(withMediaType: .audio)[0]
    try! aTrack.insertTimeRange(CMTimeRange(start: .zero, duration: track.timeRange.duration), of: track, at: t(s.start + s.offset))
}
let outURL = URL(fileURLWithPath: out)
try? FileManager.default.removeItem(at: outURL)
let export = AVAssetExportSession(asset: comp, presetName: AVAssetExportPreset1920x1080)!
export.outputURL = outURL
export.outputFileType = .mp4
export.timeRange = CMTimeRange(start: .zero, duration: t(tl.total))
let exported = DispatchSemaphore(value: 0)
export.exportAsynchronously { exported.signal() }
exported.wait()
print("export status", export.status.rawValue, export.error?.localizedDescription ?? "ok")
let result = AVURLAsset(url: outURL)
print(String(format: "duration %.3f s, video tracks %d, audio tracks %d", CMTimeGetSeconds(result.duration),
             result.tracks(withMediaType: .video).count, result.tracks(withMediaType: .audio).count))
