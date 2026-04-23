# Presentation Script: The Zen-Spanner Project

## 1. The Hook (0:00 - 0:30)
"Good morning, Professor. Imagine if Google Maps could reduce its road network data by 50% while still giving you routes that are within 10% of the shortest path. This isn't just a space-saving dream—it's the power of the **Zen-Spanner**. Our project implements the state-of-the-art Baswana-Sen algorithm and introduces a novel optimization that makes it even better."

## 2. The Core Algorithm (0:30 - 1:30)
"At the heart of our project is the **Baswana-Sen randomized clustering algorithm**. Unlike traditional greedy methods that take $O(mn)$ time, Baswana-Sen runs in near-linear $O(m)$ time. We've implemented this in both **Python**, for its rich data ecosystem, and **C++**, achieving sub-millisecond execution on 1,000-node graphs."

## 3. Our Innovation: The Zen-Spanner (1:30 - 2:30)
"But we didn't stop at the textbook implementation. We developed the **Zen-Spanner (ZS)**. By using **degree-weighted sampling**, we ensure that critical hubs are captured early. We then apply a **Greedy Pruning phase** that removes redundant probabilistic edges. The result? **A 17% to 50% improvement** in edge density over the standard algorithm without ever violating the stretch guarantee."

## 4. Real-World Applications (2:30 - 3:30)
"We've tested this on real road networks from Hyderabad and social graphs from SNAP. But more importantly, we conducted an impact study on **Satellite Constellations**. In the hyper-dynamic environment of LEO satellites like Starlink, the Zen-Spanner provides a robust, low-overhead routing backbone that saves critical battery power in space."

## 5. The Demo (3:30 - 5:00)
"Now, let's look at the **Interactive D3 Visualizer**. You can see the spanner thinning out in real-time as we increase the stretch factor *t*. Watch how the clusters form and how our algorithm intelligently bridges them. This is the Zen-Spanner: Theoretical optimality meeting practical engineering."

## 6. Closing
"We've integrated history, theory, and novel optimization into a single robust package. We are now open for questions. Thank you."
