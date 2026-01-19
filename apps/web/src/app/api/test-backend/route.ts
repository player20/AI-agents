import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export async function GET() {
  try {
    console.log(`[Test] Checking backend at: ${BACKEND_URL}`)
    const response = await fetch(`${BACKEND_URL}/`, {
      method: 'GET',
    })

    if (!response.ok) {
      return NextResponse.json({
        success: false,
        error: `Backend returned ${response.status}`,
        backendUrl: BACKEND_URL
      })
    }

    const data = await response.json()
    return NextResponse.json({
      success: true,
      backend: data,
      backendUrl: BACKEND_URL
    })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: String(error),
      backendUrl: BACKEND_URL
    })
  }
}
