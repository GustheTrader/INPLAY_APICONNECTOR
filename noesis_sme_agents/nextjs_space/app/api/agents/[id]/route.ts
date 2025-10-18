
import { getServerSession } from 'next-auth'
import { NextRequest, NextResponse } from 'next/server'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const agent = await prisma.agent.findFirst({
      where: {
        id: params.id,
        userId: session.user.id
      },
      include: {
        conversations: {
          orderBy: {
            updatedAt: 'desc'
          },
          take: 5
        },
        _count: {
          select: {
            conversations: true,
            traces: true
          }
        }
      }
    })

    if (!agent) {
      return NextResponse.json({ error: 'Agent not found' }, { status: 404 })
    }

    return NextResponse.json({ agent })
  } catch (error) {
    console.error('Error fetching agent:', error)
    return NextResponse.json(
      { error: 'Failed to fetch agent' },
      { status: 500 }
    )
  }
}

export async function PUT(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { name, description, configuration, isActive } = await req.json()

    const agent = await prisma.agent.updateMany({
      where: {
        id: params.id,
        userId: session.user.id
      },
      data: {
        ...(name && { name }),
        ...(description !== undefined && { description }),
        ...(configuration && { configuration }),
        ...(isActive !== undefined && { isActive })
      }
    })

    if (agent.count === 0) {
      return NextResponse.json({ error: 'Agent not found' }, { status: 404 })
    }

    // Fetch updated agent
    const updatedAgent = await prisma.agent.findFirst({
      where: {
        id: params.id,
        userId: session.user.id
      },
      include: {
        _count: {
          select: {
            conversations: true,
            traces: true
          }
        }
      }
    })

    return NextResponse.json({ agent: updatedAgent })
  } catch (error) {
    console.error('Error updating agent:', error)
    return NextResponse.json(
      { error: 'Failed to update agent' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const agent = await prisma.agent.updateMany({
      where: {
        id: params.id,
        userId: session.user.id
      },
      data: {
        isActive: false
      }
    })

    if (agent.count === 0) {
      return NextResponse.json({ error: 'Agent not found' }, { status: 404 })
    }

    return NextResponse.json({ message: 'Agent deleted successfully' })
  } catch (error) {
    console.error('Error deleting agent:', error)
    return NextResponse.json(
      { error: 'Failed to delete agent' },
      { status: 500 }
    )
  }
}
