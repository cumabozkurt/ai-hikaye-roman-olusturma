// AI Hikaye & Roman Oluşturma — OpenCode 1.x eklentisi (adlandırılmış eklenti işlevi).
// Kontrol mantığının tamamı Python çekirdeğindedir: .hikaye/kancalar/hikaye_kanca.py
// hikaye-kurulum tarafından OpenCode 1.x algılandığında üretilir; elle düzenlemeyin.
import { execFileSync } from "node:child_process"
import * as fs from "node:fs"
import * as path from "node:path"

function kancaCalistir(kok: string, olay: string, yuk: Record<string, unknown>): Record<string, unknown> | null {
  const betik = path.join(kok, ".hikaye", "kancalar", "hikaye_kanca.py")
  if (!fs.existsSync(betik) || !fs.existsSync(path.join(kok, ".hikaye-kurulu"))) return null
  for (const py of ["python3", "python"]) {
    try {
      const cikti = execFileSync(py, [betik, olay, "--ev", "opencode"], {
        cwd: kok, input: JSON.stringify(yuk), encoding: "utf-8", timeout: 15000,
        env: { ...process.env, HIKAYE_PROJE_KOKU: kok },
      }).trim()
      return cikti ? (JSON.parse(cikti) as Record<string, unknown>) : null
    } catch (hata: unknown) {
      if ((hata as { code?: string })?.code === "ENOENT") continue
      return null
    }
  }
  return null
}

export const AiHikayeKancalari = async ({ directory, worktree }: { directory: string; worktree?: string }) => {
  const kok = worktree || directory
  // 1.x "after" olayında araç argümanları gelmez; "before" olayında çağrı kimliğiyle saklanır.
  const argumanlar = new Map<string, Record<string, unknown>>()
  return {
    "tool.execute.before": async (girdi: { tool: string; callID?: string }, cikti: { args: Record<string, unknown> }) => {
      if (!["write", "edit", "patch", "bash"].includes(girdi.tool)) return
      if (girdi.callID) argumanlar.set(girdi.callID, cikti.args ?? {})
      const c = kancaCalistir(kok, "yazi-oncesi", { tool_name: girdi.tool, tool_input: cikti.args ?? {}, cwd: directory })
      if (c && c.engelle === true) throw new Error(String(c.neden))
    },
    "tool.execute.after": async (girdi: { tool: string; callID?: string }, cikti: { output?: string }) => {
      const args = girdi.callID ? argumanlar.get(girdi.callID) : undefined
      if (girdi.callID) argumanlar.delete(girdi.callID)
      if (!args || !["write", "edit", "patch"].includes(girdi.tool)) return
      const c = kancaCalistir(kok, "yazi-sonrasi", { tool_name: girdi.tool, tool_input: args, cwd: directory })
      if (c && typeof c.not === "string" && c.not) cikti.output = `${cikti.output ?? ""}\n\n${c.not}`
    },
    "experimental.session.compacting": async (_girdi: unknown, cikti: { context: string[] }) => {
      const c = kancaCalistir(kok, "sikistirma-oncesi", {})
      if (c && typeof c.not === "string") cikti.context.push(c.not)
    },
  }
}
