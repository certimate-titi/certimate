'use client';

import { createContext, useContext, ReactNode } from 'react';

const EmbedContext = createContext(false);

export function EmbedProvider({ children }: { children: ReactNode }) {
  return <EmbedContext.Provider value={true}>{children}</EmbedContext.Provider>;
}

export function useIsEmbedded() {
  return useContext(EmbedContext);
}
