sample_prompt = """The following is cpp code snippet from code base, please explain it in less than 10 sentences in English. The description should explain what the code does overall,  without using specific variable names or function names. The code:\n\n void mergeSort(vector<int> &v, int n){
	if(n < 2) return;
	int mid = n/2;
	vector<int> left(mid), right(n-mid);
	for(int i = 0; i < mid; i++)
		left[i] = v[i];
	for(int i = mid ; i < (int)v.size(); i++)
		right[i - mid] = v[i];
	mergeSort(left, mid);
	mergeSort(right, n - mid);
	merge(v, left, mid, right, n-mid);
}
"""
sample_ans="""This function is responsible for breaking the problem into subproblems.
    This uses recursion to divide the array into left and right array and we stop or return when our left and right array size becomes 1.Finally as the recursion backtracks we call merge above that combines these left and right arrays into one sorted array.Thus, doing so gives us our sorted array."""
    