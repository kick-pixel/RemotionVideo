# 什么是 React Server Components (RSC)？

React Server Components 是一种在服务器端渲染 React 组件的新架构。与传统的客户端渲染不同，服务端组件只在服务器上执行，它们不会向客户端发送任何 JavaScript 代码，从而极大减小了前端 JS bundle 的体积，并提升了页面的加载性能与交互体验。

传统 React 会在客户端挂载整个应用，并通过 JavaScript 获取数据，这会导致“瀑布流”式的请求问题。而 RSC 允许我们在服务端就直接读取数据库或文件系统，处理完数据后直接将渲染好的 HTML/JSON 抛给游览器。

同时它还能和传统的 Client Components 搭配使用，保持 UI 互动性，可以说 RSC 融合了 SSR 的性能与 CSR 的体验。
