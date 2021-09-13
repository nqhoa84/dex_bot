Initial version is forked from mr Kiet version. 
Functions: 
V3.0: With each pair 
-- detect pump and dump, price is over/below a constant 
-- price is calculate every block

Next: 
-- calculate price impact >> applied slippage is more accurate. 
-- check balance to buy/sell all or ignore the buy/sell trans if not enough. 
-- change how to handle thread: 
	Now: 1 thread / each pair, use sleep as interval >> always alive 
	Next: use timer to open one thread to process all pair.