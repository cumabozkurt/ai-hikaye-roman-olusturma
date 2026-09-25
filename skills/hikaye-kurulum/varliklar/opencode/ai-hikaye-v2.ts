// AI Hikaye & Roman Oluşturma — OpenCode 2.x eklentisi (default export { id, setup }).
// Kontrol mantığının tamamı Python çekirdeğindedir: .hikaye/kancalar/hikaye_kanca.py
// Bu dosya yalnızca OpenCode olaylarını çekirdeğe aktarır. hikaye-kurulum tarafından üretilir; elle düzenlemeyin.
import { execFileSync } from "node:child_process"
import * as fs from "node:fs"
import * as path from "node:path"

type Girdi = Record<string, unknown>

function projeKoku(dizin: string): string {
  try {
    return execFileSync("git", ["rev-parse", "--show-toplevel"], { cwd: dizin, encoding: "utf-8", stdio: ["ignore", "pipe", "ignore"] }).trim() || dizin
  } catch {
    return dizin
  }
}

function kancaCalistir(kok: string, olay: string, yuk: Girdi): Record<string, unknown> | null {
  const betik = path.join(kok, ".hikaye", "kancalar", "hikaye_kanca.py")
  if (!fs.existsSync(betik) || !fs.existsSync(path.join(kok, ".hikaye-kurulu"))) return null
  for (const py of ["python3", "python"]) {
    try {
      const cikti = execFileSync(py, [betik, olay, "--ev", "opencode"], {
        cwd: kok,
        input: JSON.stringify(yuk),
        encoding: "utf-8",
        timeout: 15000,
        env: { ...process.env, HIKAYE_PROJE_KOKU: kok },
      }).trim()
      return cikti ? (JSON.parse(cikti) as Record<string, unknown>) : null
    } catch (hata: unknown) {
      if ((hata as { code?: string })?.code === "ENOENT") continue
      return null // kanca hatası akışı kilitlemez
    }
  }
  return null
}

function notEkle(sonuc: { content?: string | ReadonlyArray<unknown>; output?: unknown }, not: string) {
  const icerik = sonuc.content
  if (typeof icerik === "string") return `${icerik}\n\n${not}`
  const taban: ReadonlyArray<unknown> = icerik && icerik.length > 0
    ? icerik
    : [{ type: "text", text: typeof sonuc.output === "string" ? sonuc.output : JSON.stringify(sonuc.output ?? "") }]
  return [...taban, { type: "text", text: not }]
}

export default {
  id: "ai-hikaye.kancalar",
  async setup(ctx: any) {
    const dizin: string = ctx.location.directory

    await ctx.session.hook("compaction", (olay: any) => {
      const c = kancaCalistir(projeKoku(dizin), "sikistirma-oncesi", {})
      if (c && typeof c.not === "string") olay.system.push({ type: "text", text: c.not })
    })

    await ctx.tool.hook("execute.before", (olay: any) => {
      if (!["write", "edit", "patch", "shell", "bash"].includes(String(olay.tool))) return
      const c = kancaCalistir(projeKoku(dizin), "yazi-oncesi", { tool_name: olay.tool, tool_input: olay.input ?? {}, cwd: dizin })
      if (c && c.engelle === true) throw new Error(String(c.neden))
    })

    await ctx.tool.hook("execute.after", (olay: any) => {
      if (olay.status !== "completed" || !["write", "edit", "patch"].includes(String(olay.tool))) return
      const c = kancaCalistir(projeKoku(dizin), "yazi-sonrasi", { tool_name: olay.tool, tool_input: olay.input ?? {}, cwd: dizin })
      if (c && typeof c.not === "string" && c.not) olay.result = { ...olay.result, content: notEkle(olay.result ?? {}, c.not) }
    })
  },
}
