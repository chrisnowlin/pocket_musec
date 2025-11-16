declare module 'find-free-port' {
  function findFreePort(
    start: number,
    end: number,
    host: string,
    callback: (err: any, port: number) => void
  ): void;
  
  export = findFreePort;
}