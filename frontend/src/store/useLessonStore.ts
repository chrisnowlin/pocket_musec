type GenerationProgress = {
  step: string
  progress: number
  message?: string
  partial_content?: string
}

type LessonStoreApi = {
  setGenerating: (generating: boolean) => void
  setGenerationProgress: (payload: GenerationProgress) => void
  addLessonContent: (content: string) => void
  completeGeneration: (content: string, metadata?: Record<string, unknown>) => void
  setError: (error: string) => void
}

const noop = () => {}

const storeState: LessonStoreApi = {
  setGenerating: noop,
  setGenerationProgress: noop,
  addLessonContent: noop,
  completeGeneration: noop,
  setError: noop,
}

export const useLessonStore = {
  getState: () => storeState,
}
