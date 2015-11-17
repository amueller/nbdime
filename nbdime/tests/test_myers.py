
from __future__ import print_function

import operator
import numpy as np
from six.moves import xrange as range

# Set to true to enable additional assertions, array access checking, and printouts
DEBUGGING = 0
import pdb

class DebuggingArray(object):
    "Debugging tool to capture array accesses."
    def __init__(self, n, dt, name):
        print("Alloc %s[%d]" % (name, n))
        self.a = np.empty(n, dtype=dt)
        self.untouchedvalue = -123456789
        self.a[:] = self.untouchedvalue
        self.w = np.zeros(n, dtype=dt)
        self.name = name

    def __getitem__(self, i):
        if not self.w[i]:
            raise RuntimeError("Trying to read unwritten location in array!")
        print("    %d <- %s[%d]" % (self.a[i], self.name, i))
        return self.a[i]

    def __setitem__(self, i, v):
        if self.w[i]:
            print("    %s[%d] <- %d (was: %d)" % (self.name, i, v, self.a[i]))
        else:
            print("    %s[%d] <- %d (first access)" % (self.name, i, v))
        self.w[i] = 1
        self.a[i] = v
        return v

def alloc_V_array(N, M, name):
    # 32 bit should be sufficient for all practical use cases
    assert max(N, M) < 2**31
    int_t = np.int32

    # Size of array should be big enough for N+M edits,
    # and thus indexing from V[V0-D] to V[V0+D], V0=N+M
    n = 2*(N + M)+1

    # Not initializing V with zeros, if the algorithms access uninitialized values that's a bug
    V = np.empty(n, dtype=int_t)

    # Enabling this allows debugging accesses to uninitialized values
    if DEBUGGING:
        V = DebuggingArray(n, int_t, name)

    return V

def greedy_forward_ses(A, B, compare=operator.__eq__):
    "The greedy LCS/SES algorithm from Fig. 2 of Myers' article."
    # Note that the article uses 1-based indexing of A and B, while here we use standard 0-based indexing
    N, M = len(A), len(B)
    if N + M == 0:
        return 0
    # Parameter to allow bounding the size of an acceptible edit script
    MAX = M + N
    # Allocate uninitialized array with minimal integer size needed
    V = alloc_V_array(N, M, "V")
    # V is indexed from -MAX to +MAX in the algorithm,
    # here indexing using V[V0 + i] to map to 0-based indices
    V0 = MAX
    V[V0+1] = 0 # Seed for first iteration, corresponding to x just outside of range
    for D in range(MAX+1):
        for k in range(-D, D+1, 2):
            if k == -D or k != D and V[V0+k-1] < V[V0+k+1]:
                # Coming from diagonal k+1, the diagonal above k, so keeping x
                x = V[V0+k+1]
            else:
                # Coming from diagonal k-1, the diagonal to the left of k, so incrementing x
                x = V[V0+k-1] + 1
            # Forward lines are centered around x-y=0
            y = x - k
            # Compare sequence elements along k-diagonal
            while x < N and y < M and compare(A[x], B[y]):
                x += 1
                y += 1
            # Store x coordinate at end of snake for this k-line
            V[V0+k] = x
            if x >= N and y >= M:
                # Return the length of the shortest edit script
                ses = D
                return ses
    raise RuntimeError("Shortest edit script length exceeds {}.".format(MAX))

def greedy_reverse_ses(A, B, compare=operator.__eq__):
    "Reverse variant of the greedy LCS/SES algorithm from Fig. 2 of Myers' article."
    # Note that the article uses 1-based indexing of A and B, while here we use standard 0-based indexing
    pdb.set_trace()

    N, M = len(A), len(B)
    delta = N - M
    if N + M == 0:
        return 0
    # Parameter to allow bounding the size of an acceptible edit script
    MAX = M + N
    # Allocate uninitialized array with minimal integer size needed
    V = alloc_V_array(N, M, "V")
    # V is indexed from -MAX to +MAX in the algorithm,
    # here indexing using V[V0 + i] to map to 0-based indices
    V0 = MAX
    V[V0+1] = N # Seed for first iteration, corresponding to x just outside of range
    for D in range(MAX+1):
        for k in range(-D, D+1, 2):
            if k == -D or k != D and V[V0+k-1] < V[V0+k+1]:
                # Coming from diagonal k+1, the diagonal to the right of k, so decrementing x
                x = V[V0+k+1] - 1
            else:
                # Coming from diagonal k-1, the diagonal below k, so keeping x
                x = V[V0+k-1]
            # Reverse lines are centered around x-y=delta
            y = x - k - delta
            # Compare sequence elements along k-diagonal
            while x >= 0 and y >= 0 and compare(A[x], B[y]):
                x -= 1
                y -= 1
            # Store x coordinate at end of snake for this k-line
            V[V0+k] = x
            if x < 0 and y < 0:
                # Return the length of the shortest edit script
                ses = D
                return ses
    raise RuntimeError("Shortest edit script length exceeds {}.".format(MAX))


def find_forward_path(A, B, V, V0, D, k, compare=operator.__eq__):
    "The greedy LCS/SES algorithm from Fig. 2 of Myers' article."
    N, M = len(A), len(B)

    if k == -D or k != D and V[V0+k-1] < V[V0+k+1]:
        # Coming from diagonal k+1, the diagonal above k, so keeping x
        x = V[V0+k+1]
    else:
        # Coming from diagonal k-1, the diagonal to the left of k, so incrementing x
        x = V[V0+k-1] + 1
    # Forward lines are centered around x-y=0
    y = x - k

    x0 = x
    y0 = y

    # Compare sequence elements along k-diagonal
    while x < N and y < M and compare(A[x], B[y]):
        x += 1
        y += 1
    # Store x coordinate at end of snake for this k-line
    V[V0+k] = x

    if DEBUGGING:
        assert x0 == N or y0 == M or (x-x0) == 0 or compare(A[x0], B[y0])
        assert x >= N or y >= M or not compare(A[x], B[y])
        for i in range(x-x0):
            assert compare(A[x0+i], B[y0+i])

    # The forward snake covers [x0,x) [y0,y)
    return x0, y0, x, y

def find_reverse_path(A, B, V, V0, D, k, delta, compare=operator.__eq__):
    "Reverse variant of the greedy LCS/SES algorithm from Fig. 2 of Myers' article."
    N, M = len(A), len(B)
    delta = N - M

    if k == -D or k != D and V[V0+k-1] < V[V0+k+1]:
        # Coming from diagonal k+1, the diagonal to the right of k, so decrementing x
        x = V[V0+k+1] - 1
    else:
        # Coming from diagonal k-1, the diagonal below k, so keeping x
        x = V[V0+k-1]
    # Reverse lines are centered around x-y=delta
    y = x - k - delta

    x0 = x
    y0 = y

    # Compare sequence elements along k-diagonal
    while x >= 0 and y >= 0 and compare(A[x], B[y]):
        x -= 1
        y -= 1
    # Store x coordinate at end of snake for this k-line
    V[V0+k] = x

    if DEBUGGING:
        assert x0 < 0 or y0 < 0 or (x0-x) == 0 or compare(A[x0], B[y0])
        assert x < 0 or y < 0 or not compare(A[x], B[y])
        for i in range(x0-x):
            assert compare(A[x0-i], B[y0-i])

    # The forward snake covers (x,x0] (y,y0]
    return x+1, y+1, x0+1, y0+1

def find_middle_snake(A, B, compare=operator.__eq__):
    N = len(A)
    M = len(B)
    delta = N - M
    odd = delta % 2 == 1
    even = not odd

    # Allocate uninitialized array with minimal integer size needed
    # V is indexed from -MAX to +MAX in the algorithm,
    # here indexing using V[V0 + i] to map to 0-based indices
    V0 = N + M
    Vf = alloc_V_array(N, M, "Vf")
    Vr = alloc_V_array(N, M, "Vr")
    Vf[V0+1] = 0 # Seed for first iteration, corresponding to x just outside of range
    Vr[V0+1] = N # Seed for first iteration, corresponding to x just outside of range

    # For an increasing number of edits
    for D in range((M+N+1)//2):
        if DEBUGGING: print("Forward", D)

        # Forward search along k-diagonals
        for k in range(-D, D+1, 2):
            if DEBUGGING: print("  k:", k)

            # Find the end of the furthest reaching forward D-path in diagonal k
            x, y, u, v = find_forward_path(A, B, Vf, V0, D, k, compare=compare)
            if DEBUGGING: print("    xyuv:", x, y, u, v)

            # Look for overlap with reverse search
            if odd and D>0 and (-(D-1) <= k-delta <= (D-1)):
                # Check if the path overlaps the furthest reaching reverse D-1-path in diagonal k
                if Vr[V0+k-delta] <= Vf[V0+k]:
                    # Length of the SES
                    ses = 2*D-1
                    # The last snake of the forward path is the middle snake
                    return ses, x, y, u, v

        if DEBUGGING: print("Reverse", D)
        # Reverse search along k-diagonals
        for k in range(-D, D+1, 2):
            if DEBUGGING: print("  k:", k)

            # Find the end of the furthest reaching reverse D-path in diagonal k+delta
            x, y, u, v = find_reverse_path(A, B, Vr, V0, D, k, delta, compare=compare)
            if DEBUGGING: print("    xyuv:", x, y, u, v)

            # Look for overlap with forward search
            if even and (-D <= k+delta <= D):
                # Check if the path overlaps the furthest reaching forward D-path in diagonal k+delta
                if Vr[V0+k] <= Vf[V0+k+delta]:
                    # Length of the SES
                    ses = 2*D
                    # The last snake of the reverse path is the middle snake
                    return ses, x, y, u, v

    raise RuntimeError("Failed to find middle snake!")

def lcs(A, B, compare=operator.__eq__):
    "Yield elements of the lcs of A and B."
    N = len(A)
    M = len(B)
    if N and M:
        # Find the middle snake. The middle snake is a sequence
        # of 0 or more diagonals where
        D, x, y, u, v = find_middle_snake(A, B, compare=compare)

        if DEBUGGING:
            assert x - y == u - v
            for i in range(u - x):
                assert compare(A[x+i], B[y+i])

        if D > 1:
            # Yield lcs of the upper/left corner rectangle
            for s in lcs(A[:x], B[:y]):
                yield s
            # Yield the middle snake
            for s in A[x:u]:
                yield s
            # Yield lcs of the lower/right corner rectangle
            for s in lcs(A[u:], B[v:]):
                yield s
        elif N < M:
            # A is shortest.
            # If only 0 or 1 edit operation is needed,
            # the shortest of A and B is the lcs.
            for s in A:
                yield s
        else:
            # B is shortest.
            for s in B:
                yield s

def test_greedy_forward_ses():
    for i in range(5):
        for j in range(5):
            assert greedy_forward_ses(list(range(i)), list(range(j))) == abs(i-j)

def test_greedy_reverse_ses():
    for i in range(5):
        for j in range(5):
            gr = greedy_reverse_ses(list(range(i)), list(range(j)))
            assert gr == abs(i-j)

def test_lcs():
    # Both empty
    assert list(lcs([], [])) == []

    # One empty
    for i in range(10):
        a = list(range(i))
        assert list(lcs(a, [])) == []
        assert list(lcs([], a)) == []

    # Equal
    for i in range(0, 10):
        a = list(range(i))
        assert list(lcs(a, a)) == a

    # Delete any single item
    for i in range(10):
        a = list(range(i))
        for j in range(len(a)):
            b = list(a)
            b.pop(j)
            assert list(lcs(a, b)) == b

    # Delete successive interleaved items
    for i in range(1, 10):
        a = list(range(i))
        b = list(a)
        for j in range(len(a)-1, 0, -2):
            b.pop(j)
            assert list(lcs(a, b)) == b

    # Insert single item anywhere
    for i in range(10):
        a = list(range(i))
        for j in range(len(a)):
            b = list(a)
            b.insert(j, 77)
            assert list(lcs(a, b)) == a

    # Insert successive interleaved items
    for i in range(1, 10):
        a = list(range(i))
        b = list(a)
        for j in range(len(a)-1, 0, -2):
            b.insert(j, len(a) + j + 1)
            assert list(lcs(a, b)) == a

def xtest_greedy_ses_with_neil_fraser_cases():
    global DEBUGGING
    DEBUGGING = False
    # Case from neil.fraser.name/writing/diff/
    assert greedy_forward_ses(list("abcab"), list("ayb")) == 3+1
    assert greedy_reverse_ses(list("abcab"), list("ayb")) == 3+1
    assert greedy_forward_ses(list("xaxcxabc"), list("abcy")) == 5+1
    #DEBUGGING = True

def test_greedy_ses_with_neil_fraser_cases():
    assert greedy_reverse_ses(list("xaxcxabc"), list("abcy")) == 5+1

def test_neil_fraser_case():
    # Case from neil.fraser.name/writing/diff/
    #assert list(lcs(list("abcab"), list("ayb"))) == ["a","b"]

    # These cases fail:
    assert list(lcs(list("abcab"), list("ayb"))) == ["a","b"]
    #assert list(lcs(list("abcb"), list("ayb"))) == ["a","b"]

    # These cases work:
    #assert list(lcs(list("abyb"), list("ayb"))) == ["a","y","b"]
    #assert list(lcs(list("ayb"), list("ayb"))) == ["a","y","b"]
