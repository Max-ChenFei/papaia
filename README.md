# single-spec

We propose a \emph{single-spec programming model} for AI agents. 

(1) At the source level, programmers define components as they do today---as ordinary functions or classes in the host language---and enrich them with lightweight annotations (e.g., required resources, running dependencies constraints).

(2) From these annotated definitions, the compiler extracts a component **specification** for each component: its name, typed inputs and outputs, behaviour (as given by the function or method body), and resource requirements. 

(3) From these specifications, our compiler derives (i) concrete placements, (ii) execution forms together with the necessary infra-bound plumbing, and (iii) agent-facing tool APIs.

## Todo
- [ ] add more executors for Slurm or k8s
- [ ] add caching to avoid always stop the container and install pip package at each run