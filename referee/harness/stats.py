
import json, math, sys
def beta_cdf(a, b, x, steps=4000):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    lb = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    f = lambda t: 0.0 if t <= 0 or t >= 1 else math.exp((a - 1) * math.log(t) + (b - 1) * math.log(1 - t) - lb)
    h = x / steps
    s = f(0) + f(x) + sum((4 if i % 2 else 2) * f(i * h) for i in range(1, steps))
    return s * h / 3
def cp_lower(x, n, alpha):
    if x <= 0: return 0.0
    if x >= n: return alpha ** (1 / n)
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if beta_cdf(x, n - x + 1, mid) > alpha: hi = mid
        else: lo = mid
    return lo
def mcnemar(b, c):
    m = b + c
    return sum(math.comb(m, k) for k in range(c, m + 1)) / 2 ** m
if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "cp_lower":
        print(json.dumps({"lb": f"{cp_lower(float(a[1]), int(a[2]), float(a[3])):.6f}"}))
    else:
        print(json.dumps({"p": f"{mcnemar(int(a[1]), int(a[2])):.6f}"}))
