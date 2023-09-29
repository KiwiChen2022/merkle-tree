import hashlib


class MerkleTree:
    def __init__(self, leafs, height):
        self.leafs = leafs
        self.height = height
        root = self.get_node(0, 0)
        self.root = root

    def get_node(self, height, index):
        max_index = 2**height - 1
        max_height = self.height
        if height > max_height:
            raise Exception("Height out of range")
        if index > max_index:
            raise Exception("Index out of range")
        if height == self.height:
            return self.leafs[index]
        else:
            left = self.get_node(height + 1, index * 2)
            right = self.get_node(height + 1, index * 2 + 1)
            return hashlib.sha256((left + right).encode()).hexdigest()

    def get_root(self):
        return self.root

    def get_merkle_path(self, index, height):
        path = []

        while height > 0:
            path.append((height, index))
            index = index // 2
            height -= 1
        return path

    def get_sibling_node(self, height, index):
        if height == 0:
            raise Exception("No sibling node at height 0 (root)")

        if index % 2 == 0:
            return self.get_node(height, index + 1)
        else:
            return self.get_node(height, index - 1)

    def get_merkle_proof(self, height, index):
        siblings = []

        path = self.get_merkle_path(index, height)

        for node in path:
            siblings.append(self.get_sibling_node(node[0], node[1]))

        proof = {
            "siblings": siblings,
            "root": self.root,
            "value": self.get_node(height, index),
            "index": index,
        }
        return proof

    def update_leaf(self, index, value):
        old_merkle_proof = self.get_merkle_proof(self.height, index)
        old_siblings = old_merkle_proof["siblings"]
        old_value = old_merkle_proof["value"]

        new_root = compute_merkle_root_from_merkle_proof(old_siblings, value, index)

        self.leafs[index] = value
        self.root = self.get_node(0, 0)
        new_merkle_proof = self.get_merkle_proof(self.height, index)

        print("old root: " + old_merkle_proof["root"])
        print("new root: ", new_root == new_merkle_proof["root"])
        print("new root: new_merkle_proof[root]: " + new_merkle_proof["root"])
        print("self.root: " + self.root)

        return {
            "old_merkle_proof": old_merkle_proof,
            "new_merkle_proof": new_merkle_proof,
        }


def compute_merkle_root_from_merkle_proof(siblings, value, index):
    for node in siblings:
        if index % 2 == 0:
            value = hashlib.sha256((value + node).encode()).hexdigest()
        else:
            value = hashlib.sha256((node + value).encode()).hexdigest()
        index = index // 2
    return value


def verify_merkle_proof(proof):
    computed_root = compute_merkle_root_from_merkle_proof(
        proof["siblings"], proof["value"], proof["index"]
    )
    return computed_root == proof["root"]


def example1():
    leafs = [
        "a",
        "b",
        "c",
        "d",
    ]
    tree = MerkleTree(leafs, 2)
    print("EX1:", tree.get_node(2, 0))
    print("EX1:", tree.get_node(1, 0))
    print("EX1: root:", tree.get_node(0, 0))

    tree.update_leaf(0, "e")


example1()


def example4():
    height = 3
    leaves = [
        "0000000000000000000000000000000000000000000000000000000000000001",  # 1
        "0000000000000000000000000000000000000000000000000000000000000003",  # 3
        "0000000000000000000000000000000000000000000000000000000000000003",  # 3
        "0000000000000000000000000000000000000000000000000000000000000007",  # 7
        "0000000000000000000000000000000000000000000000000000000000000004",  # 4
        "0000000000000000000000000000000000000000000000000000000000000009",  # 9
        "0000000000000000000000000000000000000000000000000000000000000000",  # 0
        "0000000000000000000000000000000000000000000000000000000000000006",  # 6
    ]

    tree = MerkleTree(leaves, height)
    print("[EX_4] the root is: " + tree.get_root())
    merkleProofOfN3_5 = tree.get_merkle_proof(3, 5)
    print("[EX_4] the merkle proof of N(3,5):\n" + str(merkleProofOfN3_5))

    computed_root = compute_merkle_root_from_merkle_proof(
        merkleProofOfN3_5["siblings"],
        merkleProofOfN3_5["value"],
        merkleProofOfN3_5["index"],
    )
    print("[EX_4] computed root: " + computed_root)
    print("[EX_4] verify merkle proof: " + str(verify_merkle_proof(merkleProofOfN3_5)))


example4()
