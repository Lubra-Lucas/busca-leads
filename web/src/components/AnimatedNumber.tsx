import { useEffect } from 'react'
import { animate, motion, useMotionValue, useTransform } from 'framer-motion'
import { nf } from '../lib/format'

export default function AnimatedNumber({ value, sufixo = '' }: { value: number; sufixo?: string }) {
  const mv = useMotionValue(0)
  const texto = useTransform(mv, (v) => nf.format(Math.round(v)) + sufixo)
  useEffect(() => {
    const c = animate(mv, value, { duration: 0.9, ease: 'easeOut' })
    return () => c.stop()
  }, [mv, value])
  return <motion.span>{texto}</motion.span>
}
