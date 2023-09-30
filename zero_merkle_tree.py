import hashlib

MerkleNodeValue = str


def hash(leftNode: MerkleNodeValue, rightNode: MerkleNodeValue) -> MerkleNodeValue:
    combined = bytes.fromhex(leftNode) + bytes.fromhex(rightNode)
    return hashlib.sha256(combined).hexdigest()


def computeZeroHashes(height: int) -> list[MerkleNodeValue]:
    currentZeroHash = "0000000000000000000000000000000000000000000000000000000000000000"
    zeroHashes = [currentZeroHash]
    for i in range(1, height + 1):
        currentZeroHash = hash(currentZeroHash, currentZeroHash)
        zeroHashes.append(currentZeroHash)
    return zeroHashes


class NodeStore:
    def __init__(self, height: int):
        self.nodes = {}
        self.height = height
        self.zeroHashes = computeZeroHashes(height)

    def contains(self, level: int, index: int) -> bool:
        # check if the node exists in the data store
        return f"{level}_{index}" in self.nodes

    def set(self, level: int, index: int, value: MerkleNodeValue):
        # set the value of the node in the data store
        self.nodes[f"{level}_{index}"] = value

    def get(self, level: int, index: int) -> MerkleNodeValue:
        if self.contains(level, index):
            # if the node is in the datastore, return it
            return self.nodes[f"{level}_{index}"]
        else:
            # if the node is NOT in the data store, return the correct zero hash for the node's level
            return self.zeroHashes[self.height - level]


class ZeroMerkleTree:
    def __init__(self, height: int):
        self.height = height
        self.nodeStore = NodeStore(height)

    def setLeaf(self, index: int, value: MerkleNodeValue):
        currentIndex = index
        currentValue = value

        oldValue = self.nodeStore.get(self.height, currentIndex)
        oldRoot = self.nodeStore.get(0, 0)

        siblings = []

        for level in range(self.height, 0, -1):
            # set the current node
            self.nodeStore.set(level, currentIndex, currentValue)
            # determine sibling
            if currentIndex % 2 == 0:
                # if the current index is even, the sibling is to the right
                rightSibling = self.nodeStore.get(level, currentIndex + 1)
                currentValue = hash(currentValue, rightSibling)
                siblings.append(rightSibling)

            else:
                # if the current index is odd, the sibling is to the left
                leftSibling = self.nodeStore.get(level, currentIndex - 1)
                # print("currentValue: " + currentValue + " leftSibling: " + leftSibling)

                currentValue = hash(leftSibling, currentValue)  # Change the order here
                siblings.append(leftSibling)

            currentIndex = currentIndex // 2

        # set the root node
        self.nodeStore.set(0, 0, currentValue)

        return {
            "index": index,
            "oldValue": oldValue,
            "oldRoot": oldRoot,
            "siblings": siblings,
            "newValue": value,
            "newRoot": currentValue,
        }

    def getRoot(self) -> MerkleNodeValue:
        return self.nodeStore.get(0, 0)

    def getProof(self, index):
        currentIndex = index
        value = self.nodeStore.get(self.height, currentIndex)
        silblings = []
        for level in range(self.height, 0, -1):
            if currentIndex % 2 == 0:
                rightSibling = self.nodeStore.get(level, currentIndex + 1)
                silblings.append(rightSibling)
            else:
                leftSibling = self.nodeStore.get(level, currentIndex - 1)
                silblings.append(leftSibling)
            currentIndex = currentIndex // 2
        return {
            "index": index,
            "value": value,
            "siblings": silblings,
            "root": self.getRoot(),
        }


class AppendOnlyMerkleTree:
    def __init__(self, height):
        self.height = height
        self.zeroHashes = computeZeroHashes(height)
        self.last_merkle_proof = {
            "siblings": self.zeroHashes,
            "root": self.zeroHashes[height],
            "value": "0000000000000000000000000000000000000000000000000000000000000000",
            "index": -1,
        }

    def appendLeaf(self, value):
        oldIndex = self.last_merkle_proof["index"]
        oldValue = self.last_merkle_proof["value"]
        oldRoot = self.last_merkle_proof["root"]
        oldSiblings = self.last_merkle_proof["siblings"]
        newIndex = oldIndex + 1
        oldMerklePath = compute_merkle_path(oldSiblings, oldIndex, oldValue)

        multiplier = 1
        siblings = []

        for level in range(0, self.height):
            oldLevelIndex = oldIndex // multiplier
            newLevelIndex = newIndex // multiplier

            if oldLevelIndex == newLevelIndex:
                # if the index is the same as the old index, the sibling is the same
                siblings.append(oldSiblings[level])
            else:
                if newLevelIndex % 2 == 0:
                    # if the index is even, the sibling is to the right
                    siblings.append(self.zeroHashes[level])
                else:
                    siblings.append(oldMerklePath[level])
                # if the index is different from the old index, the sibling is the zero hash
            multiplier *= 2

        newRoot = compute_merkle_root_from_merkle_proof(siblings, value, newIndex)

        # set the last merkle proof
        self.last_merkle_proof = {
            "index": newIndex,
            "value": value,
            "siblings": siblings,
            "root": newRoot,
        }

        return {
            "index": newIndex,
            "oldValue": "0000000000000000000000000000000000000000000000000000000000000000",
            "oldRoot": oldRoot,
            "siblings": siblings,
            "newValue": value,
            "newRoot": newRoot,
        }


def compute_merkle_path(siblings, index, value):
    currentIndex = index
    currentValue = value
    path = [value]
    for level in range(len(siblings)):
        if currentIndex % 2 == 0:
            # if the index is even, the sibling is to the right
            currentValue = hash(currentValue, siblings[level])
        else:
            currentValue = hash(siblings[level], currentValue)
        path.append(currentValue)
        currentIndex = currentIndex // 2
    return path


def verifyDeltaMerkleProof(deltaMerkleProof):
    # verify the delta merkle proof
    index = deltaMerkleProof["index"]
    oldValue = deltaMerkleProof["oldValue"]
    oldRoot = deltaMerkleProof["oldRoot"]
    siblings = deltaMerkleProof["siblings"]
    newValue = deltaMerkleProof["newValue"]
    newRoot = deltaMerkleProof["newRoot"]

    return verify_merkle_proof(
        {"root": oldRoot, "siblings": siblings, "value": oldValue, "index": index}
    ) and verify_merkle_proof(
        {"root": newRoot, "siblings": siblings, "value": newValue, "index": index}
    )


def compute_merkle_root_from_merkle_proof(siblings, value, index):
    for node in siblings:
        if index % 2 == 0:
            value = hash(value, node)
        else:
            value = hash(node, value)
        index = index // 2
    return value


def verify_merkle_proof(proof):
    computed_root = compute_merkle_root_from_merkle_proof(
        proof["siblings"], proof["value"], proof["index"]
    )
    return computed_root == proof["root"]


def example2():
    leavesToSet = [
        "0000000000000000000000000000000000000000000000000000000000000001",  # 1
        "0000000000000000000000000000000000000000000000000000000000000003",  # 3
        "0000000000000000000000000000000000000000000000000000000000000003",  # 3
        "0000000000000000000000000000000000000000000000000000000000000007",  # 7
        "0000000000000000000000000000000000000000000000000000000000000004",  # 4
        "0000000000000000000000000000000000000000000000000000000000000002",  # 2
        "0000000000000000000000000000000000000000000000000000000000000000",  # 0
        "0000000000000000000000000000000000000000000000000000000000000006",  # 6
    ]
    tree = ZeroMerkleTree(3)
    for i in range(len(leavesToSet)):
        tree.setLeaf(i, leavesToSet[i])
    print("[example2] the root is: " + tree.getRoot())


# example2()


def example3():
    leavesToSet = [
        "0000000000000000000000000000000000000000000000000000000000000001",  # 1
        "0000000000000000000000000000000000000000000000000000000000000003",  # 3
        "0000000000000000000000000000000000000000000000000000000000000003",  # 3
        "0000000000000000000000000000000000000000000000000000000000000007",  # 7
        "0000000000000000000000000000000000000000000000000000000000000004",  # 4
        "0000000000000000000000000000000000000000000000000000000000000002",  # 2
        "0000000000000000000000000000000000000000000000000000000000000000",  # 0
        "0000000000000000000000000000000000000000000000000000000000000006",  # 6
    ]
    tree = ZeroMerkleTree(3)
    deltaMerkleProofs = []
    for i in range(len(leavesToSet)):
        merkleProof = tree.setLeaf(i, leavesToSet[i])
        deltaMerkleProofs.append(merkleProof)

    # verify the delta merkle proofs
    for i in range(len(deltaMerkleProofs)):
        deltaProof = deltaMerkleProofs[i]
        if not verifyDeltaMerkleProof(deltaProof):
            print(
                "[example3] ERROR: delta merkle proof for index "
                + str(deltaProof["index"])
                + " is INVALID"
            )
            raise Exception("invalid delta merkle proof")

        elif (
            i > 0
            and deltaMerkleProofs[i]["oldRoot"] != deltaMerkleProofs[i - 1]["newRoot"]
        ):
            print(
                "oldValue: "
                + deltaMerkleProofs[i]["oldRoot"]
                + " newValue: "
                + deltaMerkleProofs[i - 1]["newRoot"]
            )
            print(
                "[example3] ERROR: delta merkle proof for index "
                + str(deltaProof["index"])
                + " is INVALID"
            )
            raise Exception("invalid delta merkle proof")
        else:
            print(
                "[example3] delta merkle proof for index "
                + str(deltaProof["index"])
                + " is valid"
            )

    # print the delta merkle proofs
    # print("[example3] the delta merkle proofs are:\n" + str(deltaMerkleProofs))

    for i in range(len(leavesToSet)):
        proof = tree.getProof(i)
        if not verify_merkle_proof(proof):
            print(
                "[example3] ERROR: merkle proof for index "
                + proof["index"]
                + " is INVALID"
            )
            raise Exception("invalid merkle proof")

        elif proof["value"] != leavesToSet[i]:
            print(
                "[example3] ERROR: merkle proof for index "
                + proof["index"]
                + " has the wrong value"
            )
            raise Exception("merkle proof value mismatch")

        else:
            print(
                "[example3] merkle proof for index " + str(proof["index"]) + " is valid"
            )

        print("merkle proof for index " + str(proof["index"]) + ": " + str(proof))


#       for(let i=0;i<leavesToSet.length;i++){
#     proof = tree.getLeaf(i);
#     if(!verifyMerkleProof(proof)){
#       print.error("[example5] ERROR: merkle proof for index "+proof.index+" is INVALID");
#       throw new Error("invalid merkle proof");
#     }else if(proof.value !== leavesToSet[i]){
#       print.error("[example5] ERROR: merkle proof for index "+proof.index+" has the wrong value");
#       throw new Error("merkle proof value mismatch");
#     }else{
#       print("[example5] merkle proof for index "+proof.index+" is valid");
#     }
#     print("merkle proof for index "+proof.index+": "+JSON.stringify(proof, null, 2));
#   }


#   for(let i=0;i<deltaMerkleProofs.length;i++){
#     const deltaProof = deltaMerkleProofs[i];

#     if(!verifyDeltaMerkleProof(deltaProof)){
#       print.error("[example3] ERROR: delta merkle proof for index "+deltaProof.index+" is INVALID");
#       throw new Error("invalid delta merkle proof");
#     }else{
#       print("[example3] delta merkle proof for index "+deltaProof.index+" is valid");
#     }

#   print("[example3] the delta merkle proofs are:\n"+JSON.stringify(deltaMerkleProofs, null, 2));

# example3()


def example6():
    tree = ZeroMerkleTree(50)
    deltaA = tree.setLeaf(
        999999999999, "0000000000000000000000000000000000000000000000000000000000000008"
    )
    deltaB = tree.setLeaf(
        1337, "0000000000000000000000000000000000000000000000000000000000000007"
    )
    proofA = tree.getProof(999999999999)
    proofB = tree.getProof(1337)
    print("verifyDeltaMerkleProof(deltaA): ", verifyDeltaMerkleProof(deltaA))
    print("verifyDeltaMerkleProof(deltaB): ", verifyDeltaMerkleProof(deltaB))
    if deltaA["newRoot"] == deltaB["oldRoot"]:
        print("deltaA.newRoot === deltaB.oldRoot: True")
    else:
        print("deltaA.newRoot === deltaB.oldRoot: False")

    print("verifyMerkleProof(proofA): ", verify_merkle_proof(proofA))
    print("verifyMerkleProof(proofB): ", verify_merkle_proof(proofB))
    print("proofA: ", proofA)
    print("proofB: ", proofB)


# example6()


def example7():
    tree = AppendOnlyMerkleTree(50)
    deltaA = tree.appendLeaf(
        "0000000000000000000000000000000000000000000000000000000000000008"
    )
    deltaB = tree.appendLeaf(
        "0000000000000000000000000000000000000000000000000000000000000007"
    )

    print(deltaA)

    print("verifyDeltaMerkleProof(deltaA): " + str(verifyDeltaMerkleProof(deltaA)))
    print("verifyDeltaMerkleProof(deltaB): " + str(verifyDeltaMerkleProof(deltaB)))

    print(
        "deltaA.newRoot === deltaB.oldRoot: ",
        str(deltaA["newRoot"] == deltaB["oldRoot"]),
    )

    print("deltaA: ", deltaA)
    print("deltaB: ", deltaB)

    for i in range(50):
        leaf = format(i, "x").zfill(64)
        result = verifyDeltaMerkleProof(tree.appendLeaf(leaf))
        print(f"verifyDeltaMerkleProof(delta[{i}]): {result}")


example7()
