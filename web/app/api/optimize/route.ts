import { NextRequest } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const response = await fetch(
      `${process.env.AUDIT_API_URL ?? process.env.NEXT_PUBLIC_AUDIT_API_URL ?? "http://localhost:8000"}/optimize-roster`,
      {
        method: "POST",
        body: await request.formData(),
        cache: "no-store",
      }
    )
    const headers = new Headers()
    for (const name of [
      "content-type",
      "content-disposition",
      "x-roster-status",
      "x-roster-penalized-changes",
      "x-roster-cell-edits",
      "x-roster-plus-changes",
    ]) {
      const value = response.headers.get(name)
      if (value) headers.set(name, value)
    }
    return new Response(response.body, { status: response.status, headers })
  } catch {
    return Response.json(
      {
        error: {
          message:
            "Could not reach the optimization service. Check that the API is running and try again.",
        },
      },
      { status: 502 }
    )
  }
}
