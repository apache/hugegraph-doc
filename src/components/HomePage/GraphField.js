import React from 'react';
import clsx from 'clsx';

// Fixed (deterministic) node/edge layout so server and client markup match
// and there is no hydration mismatch. Coordinates are in a 0..100 viewBox.
const NODES = [
  [10, 22], [24, 12], [20, 46], [38, 30], [33, 64],
  [50, 18], [52, 48], [48, 78], [66, 34], [63, 66],
  [78, 20], [80, 52], [76, 80], [90, 38], [92, 70],
  [14, 78], [30, 88], [62, 12], [88, 12], [44, 50],
];

const EDGES = [
  [0, 1], [0, 2], [1, 3], [2, 3], [2, 4], [3, 5], [3, 6],
  [4, 7], [5, 6], [5, 17], [6, 8], [6, 9], [7, 9], [8, 10],
  [8, 11], [9, 11], [9, 12], [10, 13], [11, 13], [11, 14],
  [12, 14], [4, 15], [15, 16], [16, 7], [17, 18], [8, 19],
  [6, 19], [3, 19],
];

const SPARSE_NODE_COUNT = 12;

export function GraphField({className, sparse = false}) {
  const nodes = sparse ? NODES.slice(0, SPARSE_NODE_COUNT) : NODES;
  const edges = sparse
    ? EDGES.filter(([a, b]) => a < SPARSE_NODE_COUNT && b < SPARSE_NODE_COUNT)
    : EDGES;

  return (
    <div className={clsx('hgGraphField', className)} aria-hidden="true">
      <svg
        className="hgGraphField__svg"
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg">
        <g className="hgGraphField__edges">
          {edges.map(([a, b], i) => (
            <line
              key={`e${i}`}
              x1={nodes[a][0]}
              y1={nodes[a][1]}
              x2={nodes[b][0]}
              y2={nodes[b][1]}
              className="hgGraphField__edge"
              style={{animationDelay: `${(i % 8) * 0.45}s`}}
            />
          ))}
        </g>
        <g className="hgGraphField__nodes">
          {nodes.map(([x, y], i) => (
            <circle
              key={`n${i}`}
              cx={x}
              cy={y}
              r={i % 5 === 0 ? 1.5 : 1}
              className="hgGraphField__node"
              style={{animationDelay: `${(i % 6) * 0.6}s`}}
            />
          ))}
        </g>
      </svg>
    </div>
  );
}

export default GraphField;
