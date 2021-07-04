# graph-dependencies:
# 	cd src \
# 	&& terragrunt graph-dependencies | dot -Tpng > ../docs/assets/dependencies.png

export-diagrams:
	$(info Exporting all Draw IO diagrams to PNG format.)
	@find ./ -type f -name "*.drawio" -exec draw.io -x -f png "{}" \;

clean: clean-terragrunt-cache

clean-terragrunt-cache:
	$(info Removing terragrunt cache.)
	@find . -type d -name ".terragrunt-cache" -prune -exec rm -rf {} \;