import time

class Solution:
    def __init__(self):
        pass
    def find_pairs(self, nums, target):
        """
        :type nums: List[int]
        :type target: int
        :rtype: List[int]
        """
        r = []
        
        for i in range(len(nums)):
            if target-nums[i] in nums[i+1:]:
                r.append((i, i+1+nums[i+1:].index(target-nums[i])))
        '''
        I'm not sure why this snippet is much slower (> 2x).
        
        for n in nums:
            if target-n in nums[nums.index(n)+1:]:
                r.append((nums.index(n), nums[nums.index(n)+1:].index(target-n)))
        '''        
        return r

if __name__ == '__main__':
    l = [i for i in range(18517) if i%2 == 0]

    s = Solution()
    start = time.time()
    print(s.find_pairs(l, 1000))
    print("time = ", time.time() - start)
    