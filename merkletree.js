const shajs = require("sha.js"); // npm install --save sha.js

function hash(leftNode, rightNode) {
  return shajs("sha256")
    .update(leftNode + rightNode, "hex")
    .digest("hex");
}

class MerkleTree {
  constructor(height, leaves) {
    this.height = height;
    this.leaves = leaves;
  }
  N(level, index) {
    if (level === this.height) {
      // if level == height, the node is a leaf,
      // so just return the value from our dataset
      return this.leaves[index];
    } else {
      // if the node is not a leaf, use our definition:
      // N(level, index) = Hash(N(level+1, index*2), N(level+1, index*2+1))
      return hash(
        this.N(level + 1, 2 * index),
        this.N(level + 1, 2 * index + 1)
      );
    }
  }
  getRoot() {
    // the node N(0,0) is always the root node
    return this.N(0, 0);
  }

  getMerkleProof(level, index) {
    // get the value of the leaf node
    const leafValue = this.N(level, index);

    // get the levels and indexes of the nodes on the leaf's merkle path
    const merklePath = getMerklePathOfNode(level, index);

    // get the levels and indexes of the siblings of the nodes on the merkle path
    const merklePathSiblings = merklePath.map((node) => {
      return getSiblingNode(node.level, node.index);
    });

    // get the values of the sibling nodes
    const siblingValues = merklePathSiblings.map((node) => {
      return this.N(node.level, node.index);
    });

    return {
      root: this.getRoot(), // the root we claim to be our tree's root
      siblings: siblingValues, // the siblings of our leaf's merkle path
      index: index, // the index of our leaf
      value: leafValue, // the value of our leaf
    };
  }

  getDeltaMerkleProof(level, index, newValue) {
    // compute the root of the leaf at index I
    const oldLeafProof = this.getMerkleProof(level, index);
    // compute the merkle root from the proof, replacing the leaf's value with the new value
    const newRoot = computeMerkleRootFromProof(
      oldLeafProof.siblings,
      index,
      newValue
    );

    // return the data from the old proof and the new proof
    return {
      index: index,
      siblings: oldLeafProof.siblings,

      oldRoot: oldLeafProof.root,
      oldValue: oldLeafProof.value,

      newRoot: newRoot,
      newValue: newValue,
    };
  }
}

function computeMerkleRootFromProof(siblings, index, value) {
  // start our merkle node path at the leaf node
  let merklePathNodeValue = value;
  let merklePathNodeIndex = index;

  // we follow the leaf's merkle path up to the root,
  // computing the merkle path's nodes using the siblings provided as we go alone
  for (let i = 0; i < siblings.length; i++) {
    const merklePathNodeSibling = siblings[i];

    if (merklePathNodeIndex % 2 === 0) {
      // if the current index of the node on our merkle path is even:
      // * merklePathNodeValue is the left hand node,
      // * merklePathNodeSibling is the right hand node
      // * parent node's value is hash(merklePathNodeValue, merklePathNodeSibling)
      merklePathNodeValue = hash(merklePathNodeValue, merklePathNodeSibling);
    } else {
      // if the current index of the node on our merkle path is odd:
      // * merklePathNodeSibling is the left hand node
      // * merklePathNodeValue is the right hand node,
      // * parent node's value is hash(merklePathNodeSibling, merklePathNodeValue)
      merklePathNodeValue = hash(merklePathNodeSibling, merklePathNodeValue);
    }

    // using our definition, the parent node of our path node is N(level-1, floor(index/2))
    merklePathNodeIndex = Math.floor(merklePathNodeIndex / 2);
  }
  return merklePathNodeValue;
}

function verifyMerkleProof(proof) {
  return (
    proof.root ===
    computeMerkleRootFromProof(proof.siblings, proof.index, proof.value)
  );
}

function verifyDeltaMerkleProof(deltaMerkleProof) {
  // split the delta merkle proof into a before and after merkle proof, reusing the same siblings and index
  const oldProof = {
    // reuse the same siblings for both old and new
    siblings: deltaMerkleProof.siblings,
    // reuse the same index for both old and new
    index: deltaMerkleProof.index,

    root: deltaMerkleProof.oldRoot,
    value: deltaMerkleProof.oldValue,
  };

  const newProof = {
    // reuse the same siblings for both old and new
    siblings: deltaMerkleProof.siblings,
    // reuse the same index for both old and new
    index: deltaMerkleProof.index,

    root: deltaMerkleProof.newRoot,
    value: deltaMerkleProof.newValue,
  };
  return verifyMerkleProof(oldProof) && verifyMerkleProof(newProof);
}

function getMerklePathOfNode(level, index) {
  const merklePath = [];
  for (let currentLevel = level; currentLevel > 0; currentLevel--) {
    merklePath.push({
      level: currentLevel,
      index: index,
    });
    index = Math.floor(index / 2);
  }
  return merklePath;
}

console.log(getMerklePathOfNode(3, 5));

function getSiblingNode(level, index) {
  // if node is the root, it has no sibling
  if (level === 0) {
    throw new Error("the root does not have a sibling");
  } else if (index % 2 === 0) {
    // if node is even, its sibling is at index+1
    return { level: level, index: index + 1 };
  } else {
    // if node is odd, its sibling is at index-1
    return { level: level, index: index - 1 };
  }
}

function example1() {
  const height = 3;
  const leaves = [
    "0000000000000000000000000000000000000000000000000000000000000001", // 1
    "0000000000000000000000000000000000000000000000000000000000000003", // 3
    "0000000000000000000000000000000000000000000000000000000000000003", // 3
    "0000000000000000000000000000000000000000000000000000000000000007", // 7
    "0000000000000000000000000000000000000000000000000000000000000004", // 4
    "0000000000000000000000000000000000000000000000000000000000000002", // 2
    "0000000000000000000000000000000000000000000000000000000000000000", // 0
    "0000000000000000000000000000000000000000000000000000000000000006", // 6
  ];
  const tree = new MerkleTree(height, leaves);
  console.log("[EX_1] the merkle tree's root is: " + tree.getRoot());
}
example1();

function example2() {
  const height = 3;
  const leaves = [
    "0000000000000000000000000000000000000000000000000000000000000001", // 1
    "0000000000000000000000000000000000000000000000000000000000000003", // 3
    "0000000000000000000000000000000000000000000000000000000000000003", // 3
    "0000000000000000000000000000000000000000000000000000000000000007", // 7
    "0000000000000000000000000000000000000000000000000000000000000004", // 4
    "0000000000000000000000000000000000000000000000000000000000000002", // 2
    "0000000000000000000000000000000000000000000000000000000000000000", // 0
    "0000000000000000000000000000000000000000000000000000000000000006", // 6
  ];
  const tree = new MerkleTree(height, leaves);
  console.log("[EX_2] before root is: " + tree.getRoot());
  // change the 2 to a 9
  tree.leaves[5] =
    "0000000000000000000000000000000000000000000000000000000000000009";
  console.log("[EX_2] after root is: " + tree.getRoot());
}
example2();

function example4() {
  const height = 3;
  const leaves = [
    "0000000000000000000000000000000000000000000000000000000000000001", // 1
    "0000000000000000000000000000000000000000000000000000000000000003", // 3
    "0000000000000000000000000000000000000000000000000000000000000003", // 3
    "0000000000000000000000000000000000000000000000000000000000000007", // 7
    "0000000000000000000000000000000000000000000000000000000000000004", // 4
    "0000000000000000000000000000000000000000000000000000000000000009", // 9
    "0000000000000000000000000000000000000000000000000000000000000000", // 0
    "0000000000000000000000000000000000000000000000000000000000000006", // 6
  ];
  const tree = new MerkleTree(height, leaves);
  console.log("[EX_4] the root is: " + tree.getRoot());
  const merkleProofOfN3_5 = tree.getMerkleProof(3, 5);

  console.log(
    "[EX_4] the merkle proof of N(3,5):\n" +
      JSON.stringify(merkleProofOfN3_5, null, 2)
  );

  console.log(
    "[EX_4] computed root: " +
      computeMerkleRootFromProof(
        merkleProofOfN3_5.siblings,
        merkleProofOfN3_5.index,
        merkleProofOfN3_5.value
      )
  );
  console.log(
    "[EX_4] verify merkle proof: " + verifyMerkleProof(merkleProofOfN3_5)
  );
}

example4();

function example5() {
  const height = 3;
  const leaves = [
    "0000000000000000000000000000000000000000000000000000000000000001", // 1
    "0000000000000000000000000000000000000000000000000000000000000003", // 3
    "0000000000000000000000000000000000000000000000000000000000000003", // 3
    "0000000000000000000000000000000000000000000000000000000000000007", // 7
    "0000000000000000000000000000000000000000000000000000000000000004", // 4
    "0000000000000000000000000000000000000000000000000000000000000009", // 9
    "0000000000000000000000000000000000000000000000000000000000000000", // 0
    "0000000000000000000000000000000000000000000000000000000000000006", // 6
  ];
  const tree = new MerkleTree(height, leaves);
  const beforeMerkleProofOfN3_5 = tree.getMerkleProof(3, 5);
  console.log(
    "[EX_5] the merkle proof of N(3,5) before change:\n" +
      JSON.stringify(beforeMerkleProofOfN3_5, null, 2)
  );
  // change 9 to 8
  tree.leaves[5] =
    "0000000000000000000000000000000000000000000000000000000000000008";

  const afterMerkleProofOfN3_5 = tree.getMerkleProof(3, 5);
  console.log(
    "[EX_5] the merkle proof of N(3,5) after change:\n" +
      JSON.stringify(afterMerkleProofOfN3_5, null, 2)
  );
}
example5();

function example6() {
  const height = 3;
  const leaves = [
    "0000000000000000000000000000000000000000000000000000000000000001", // 1
    "0000000000000000000000000000000000000000000000000000000000000003", // 3
    "0000000000000000000000000000000000000000000000000000000000000003", // 3
    "0000000000000000000000000000000000000000000000000000000000000007", // 7
    "0000000000000000000000000000000000000000000000000000000000000004", // 4
    "0000000000000000000000000000000000000000000000000000000000000009", // 9
    "0000000000000000000000000000000000000000000000000000000000000000", // 0
    "0000000000000000000000000000000000000000000000000000000000000006", // 6
  ];
  const tree = new MerkleTree(height, leaves);

  const deltaMerkleProofOfN3_5 = tree.getDeltaMerkleProof(
    3,
    5,
    "0000000000000000000000000000000000000000000000000000000000000008"
  );
  console.log(
    "[EX_6] delta merkle proof of changing N(3,5) from 9 to 8:\n" +
      JSON.stringify(deltaMerkleProofOfN3_5, null, 2)
  );
  console.log(
    "[EX_6] verify delta merkle proof: " +
      verifyDeltaMerkleProof(deltaMerkleProofOfN3_5)
  );
}

example6();
