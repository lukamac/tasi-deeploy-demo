function dr
	docker run --rm --tty --mount type=bind,src=(pwd),dst=/demo tasi-demo bash -c "$argv"
end
