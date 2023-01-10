import LawOrionIcon from '@/components/law-orion-icon';
import useComparison from '@/lib/comparison';

export default function CompareLink() {
    const { comparisons } = useComparison();

    return (
        <>
            <LawOrionIcon className="svg-icon" />
            { comparisons.length > 0 && (
                <div className="navbar-icon-link-badge">
                    { comparisons.length }
                </div>
            )}
        </>
    )
}
