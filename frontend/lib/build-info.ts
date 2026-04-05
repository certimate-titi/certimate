export const BUILD_INFO = {
  version: '0.3.1',
  commit: process.env.NEXT_PUBLIC_BUILD_COMMIT || 'dev',
  buildTime: process.env.NEXT_PUBLIC_BUILD_TIME || 'dev',
};
