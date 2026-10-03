package com.skyfx.client.glint;

import org.jspecify.annotations.Nullable;

import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.packs.repository.PackRepository;

import net.fabricmc.fabric.api.resource.v1.ResourceLoader;
import net.fabricmc.fabric.api.resource.v1.pack.PackActivationType;
import net.fabricmc.loader.api.ModContainer;

import com.skyfx.client.SkyFXClient;
import com.skyfx.client.config.GlintType;

/**
 * Custom glints are built-in resource packs that override the vanilla glint shader. Switching glints enables the
 * matching pack (and disables the others), then lets Minecraft reload its resources.
 */
public final class GlintManager {
	private GlintManager() {
	}

	public static void registerPacks(ModContainer mod) {
		for (GlintType type : GlintType.values()) {
			String pack = type.packName();
			if (pack == null) continue;
			boolean ok = ResourceLoader.registerBuiltinPack(
					Identifier.fromNamespaceAndPath(SkyFXClient.MOD_ID, pack),
					mod,
					Component.translatable("skyfx.pack." + pack),
					type == GlintType.PALM ? PackActivationType.DEFAULT_ENABLED : PackActivationType.NORMAL);
			if (!ok) {
				SkyFXClient.LOGGER.warn("Could not register the built-in glint pack {}", pack);
			}
		}
	}

	/** The glint that is active right now, read from the selected resource packs. */
	public static GlintType current() {
		PackRepository repository = Minecraft.getInstance().getResourcePackRepository();
		for (GlintType type : GlintType.values()) {
			String id = packId(repository, type);
			if (id != null && repository.getSelectedIds().contains(id)) return type;
		}
		return GlintType.VANILLA;
	}

	/** Enables the pack of {@code wanted}, disables the other glint packs and reloads resources if anything changed. */
	public static void apply(GlintType wanted) {
		Minecraft minecraft = Minecraft.getInstance();
		PackRepository repository = minecraft.getResourcePackRepository();
		boolean changed = false;
		for (GlintType type : GlintType.values()) {
			String id = packId(repository, type);
			if (id == null) continue;
			changed |= type == wanted ? repository.addPack(id) : repository.removePack(id);
		}
		if (changed) {
			// saves options.txt and reloads the resource packs when the selection changed
			minecraft.options.updateResourcePacks(repository);
		}
	}

	private static @Nullable String packId(PackRepository repository, GlintType type) {
		String pack = type.packName();
		if (pack == null) return null;
		String expected = SkyFXClient.MOD_ID + ":" + pack;
		if (repository.isAvailable(expected)) return expected;
		for (String id : repository.getAvailableIds()) {
			if (id.endsWith(pack)) return id;
		}
		return null;
	}
}
